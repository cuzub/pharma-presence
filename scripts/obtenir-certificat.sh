#!/bin/sh
# Première obtention du certificat HTTPS Let's Encrypt (à lancer une seule fois sur le serveur).
# Pré-requis : DNS du domaine pointant vers le Raspberry Pi, ports 80 et 443 redirigés vers lui.
set -eu
cd "$(dirname "$0")/.."
. ./.env
: "${DOMAINE:?DOMAINE manquant dans .env}"
: "${EMAIL_LETSENCRYPT:?EMAIL_LETSENCRYPT manquant dans .env}"

COMPOSE="docker compose -f deploy/compose/docker-compose.yml --env-file .env"

$COMPOSE up -d nginx
$COMPOSE run --rm --entrypoint certbot certbot certonly --webroot -w /var/www/certbot \
    -d "$DOMAINE" --email "$EMAIL_LETSENCRYPT" --agree-tos --no-eff-email
# Redémarre nginx pour passer en configuration HTTPS.
$COMPOSE restart nginx
echo "Certificat obtenu : https://$DOMAINE"
