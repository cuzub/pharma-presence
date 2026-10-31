#!/usr/bin/env bash
# Déploie une version publiée de la pharmacie sur le Raspberry Pi, sous ~/pharmacie.
#
# Usage :
#   ./scripts/deployer-rpi.sh            # déploie le dernier tag git local vX.Y.Z
#   ./scripts/deployer-rpi.sh 1.2.0      # déploie une version explicite
#
# Idempotent : les secrets du .env sont générés une seule fois, sur le RPi, et ne quittent jamais la machine.
# La configuration nginx de Pedalog est sauvegardée puis testée avant rechargement ; en cas d'échec, elle est restaurée.

set -euo pipefail

RPI_HOTE="${RPI_HOTE:-david@raspberrypi.local}"
RPI_CLE="${RPI_CLE:-/Users/davidbouchard/Dropbox/IoT/ssh_keys/id_rsa}"
DOSSIER_RPI='~/pharmacie'
CONTENEUR_NGINX="pedalog-nginx"
FICHIER_NGINX='~/pedalog/nginx/conf.d/pedalog.prod.conf'
URL_PUBLIQUE="https://app.pedalog.fr/pharmacie"

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"

SSH=(ssh -i "$RPI_CLE" -o BatchMode=yes "$RPI_HOTE")

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  sed -n '2,8p' "$0" | sed 's/^# \{0,1\}//'
  exit 0
fi

if [ -n "${1:-}" ]; then
  VERSION="$1"
else
  VERSION="$(git tag --list 'v[0-9]*.[0-9]*.[0-9]*' --sort=-v:refname | head -n 1 | sed 's/^v//')"
fi

if [ -z "$VERSION" ] || ! printf '%s' "$VERSION" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+$'; then
  echo "Erreur : version introuvable ou invalide ('${VERSION:-vide}'). Publiez d'abord avec scripts/publier-images.sh." >&2
  exit 1
fi

echo "Déploiement de la version ${VERSION} sur ${RPI_HOTE}"

# 1. Préparation du dossier, génération unique des secrets, mise à jour de la version.
"${SSH[@]}" "bash -s -- '$VERSION'" <<'DISTANT'
set -euo pipefail
VERSION="$1"
DOSSIER="$HOME/pharmacie"
mkdir -p "$DOSSIER/data/postgres" "$DOSSIER/data/backups" "$DOSSIER/nginx-sauvegardes"
chmod 700 "$DOSSIER"
if [ ! -f "$DOSSIER/.env" ]; then
  {
    echo "POSTGRES_PASSWORD=$(openssl rand -hex 24)"
    echo "SECRET_KEY=$(openssl rand -hex 32)"
    echo "JWT_SECRET_KEY=$(openssl rand -hex 32)"
    echo "BACKUP_ENCRYPTION_PASSPHRASE=$(openssl rand -hex 32)"
  } > "$DOSSIER/.env"
  chmod 600 "$DOSSIER/.env"
  echo "Fichier .env créé avec des secrets générés sur le Raspberry Pi."
fi
if grep -q '^PHARMA_VERSION=' "$DOSSIER/.env"; then
  sed -i.tmp "s/^PHARMA_VERSION=.*/PHARMA_VERSION=$VERSION/" "$DOSSIER/.env" && rm -f "$DOSSIER/.env.tmp"
else
  echo "PHARMA_VERSION=$VERSION" >> "$DOSSIER/.env"
fi
DISTANT

# 2. Copie du fichier compose, puis téléchargement et démarrage.
scp -i "$RPI_CLE" -o BatchMode=yes deploy/compose/docker-compose.rpi.yml "$RPI_HOTE:pharmacie/docker-compose.yml"
"${SSH[@]}" 'cd ~/pharmacie && docker compose pull && docker compose up -d --remove-orphans'

# 3. Vérification de santé du backend, depuis le réseau Docker partagé avec Pedalog.
echo "Attente du backend…"
"${SSH[@]}" 'for i in $(seq 1 30); do
  if docker exec pedalog-nginx wget -qO- http://pharma-backend:5000/api/health 2>/dev/null; then echo; exit 0; fi
  sleep 2
done
echo "Le backend ne répond pas. Journaux :" >&2
docker logs --tail 40 pharma-backend >&2
exit 1'

# 4. Intégration de la route /pharmacie dans nginx (une seule fois, avec sauvegarde et restauration automatique).
SNIPPET="$REPO_DIR/deploy/nginx/pharmacie.conf.snippet"
if "${SSH[@]}" "grep -q '# Pharmacie, servie' $FICHIER_NGINX"; then
  echo "Route /pharmacie déjà présente dans nginx."
else
  echo "Ajout de la route /pharmacie dans la configuration nginx de Pedalog…"
  "${SSH[@]}" 'cat > /tmp/pharmacie.snippet' < "$SNIPPET"
  "${SSH[@]}" "set -euo pipefail
    f=$FICHIER_NGINX
    sauvegarde=\$HOME/pharmacie/nginx-sauvegardes/pedalog.prod.conf.\$(date +%Y%m%d_%H%M%S)
    cp \"\$f\" \"\$sauvegarde\"
    awk -v snip=/tmp/pharmacie.snippet '
      /^    location \\/ \\{/ { n++; if (n == 2) { while ((getline l < snip) > 0) print \"    \" l; print \"\" } }
      { print }
    ' \"\$f\" > /tmp/pedalog.nouveau.conf
    # Écriture sur place : conserve l'inode monté dans le conteneur nginx.
    cat /tmp/pedalog.nouveau.conf > \"\$f\"
    rm -f /tmp/pedalog.nouveau.conf /tmp/pharmacie.snippet
    if docker exec $CONTENEUR_NGINX nginx -t >/tmp/nginx-test.log 2>&1; then
      docker exec $CONTENEUR_NGINX nginx -s reload
      echo \"nginx rechargé (sauvegarde : \$sauvegarde)\"
    else
      cat \"\$sauvegarde\" > \"\$f\"
      echo 'Configuration nginx invalide : restaurée.' >&2
      cat /tmp/nginx-test.log >&2
      exit 1
    fi"
fi

# 5. Vérification publique.
echo "Vérification de ${URL_PUBLIQUE}/api/health"
curl -fsS "${URL_PUBLIQUE}/api/health" && echo
echo "Déploiement de la version ${VERSION} terminé."
