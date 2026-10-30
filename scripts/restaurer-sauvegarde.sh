#!/bin/sh
# Restaure une sauvegarde chiffrée dans la base de production.
# Usage : scripts/restaurer-sauvegarde.sh data/backups/presence_AAAAMMJJ_HHMMSS.dump.gpg
# ATTENTION : remplace toutes les données actuelles.
set -eu
cd "$(dirname "$0")/.."
. ./.env
fichier="${1:?Indiquez le fichier de sauvegarde à restaurer}"
[ -f "$fichier" ] || { echo "Fichier introuvable : $fichier" >&2; exit 1; }

printf 'Toutes les données actuelles vont être remplacées par %s. Continuer ? (oui/non) ' "$fichier"
read -r reponse
[ "$reponse" = "oui" ] || { echo "Annulé."; exit 1; }

COMPOSE="docker compose -f deploy/compose/docker-compose.yml --env-file .env"
$COMPOSE stop backend
gpg --batch --pinentry-mode loopback --passphrase "$BACKUP_ENCRYPTION_PASSPHRASE" --decrypt "$fichier" |
    $COMPOSE exec -T db pg_restore -U "${POSTGRES_USER:-presence}" -d "${POSTGRES_DB:-presence}" --clean --if-exists --no-owner
$COMPOSE start backend
echo "Restauration terminée."
