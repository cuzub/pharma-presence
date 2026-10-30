#!/bin/sh
# Choisit la configuration HTTPS si le certificat Let's Encrypt existe, sinon le mode d'amorçage HTTP.
set -eu
: "${DOMAINE:?La variable DOMAINE est obligatoire}"

if [ -f "/etc/letsencrypt/live/${DOMAINE}/fullchain.pem" ]; then
    modele=/etc/nginx/modeles/https.conf.template
else
    modele=/etc/nginx/modeles/http.conf.template
    echo "Aucun certificat pour ${DOMAINE} : démarrage en mode d'amorçage HTTP." >&2
fi
envsubst '${DOMAINE}' < "$modele" > /etc/nginx/conf.d/default.conf
