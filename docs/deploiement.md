# Déploiement sur Raspberry Pi

## Pré-requis

- Raspberry Pi 4 ou 5 (64 bits) avec Raspberry Pi OS Lite, Docker et le plugin Compose.
- Un nom de domaine (ex. `presence.ma-pharmacie.fr`) dont l'enregistrement DNS pointe vers
  l'adresse IP publique de la box.
- Sur la box : redirection des ports 80 et 443 vers le Raspberry Pi.

## Première installation

```bash
git clone <dépôt> pharma-presence && cd pharma-presence
cp .env.example .env
# Remplir .env : DOMAINE, EMAIL_LETSENCRYPT, POSTGRES_PASSWORD, SECRET_KEY, JWT_SECRET_KEY,
# BACKUP_ENCRYPTION_PASSPHRASE (générer chaque secret avec : openssl rand -base64 48)
chmod 600 .env

COMPOSE="docker compose -f deploy/compose/docker-compose.yml --env-file .env"
$COMPOSE up -d --build            # nginx démarre en mode d'amorçage (HTTP, sans certificat)
scripts/obtenir-certificat.sh     # obtient le certificat Let's Encrypt et passe nginx en HTTPS

# Compte de la pharmacienne : un mot de passe provisoire est affiché, à changer à la 1re connexion
# (--nom est facultatif : il définit le nom affiché sur la ligne IK, sinon l'identifiant est utilisé)
$COMPOSE exec backend flask creer-admin pharmacienne --nom Elise
```

> ⚠️ Conservez `BACKUP_ENCRYPTION_PASSPHRASE` en lieu sûr (gestionnaire de mots de passe,
> enveloppe au coffre…) : sans elle, les sauvegardes sont illisibles.

Le certificat est renouvelé automatiquement (service `certbot`), et nginx recharge sa configuration
toutes les 6 h.

## Mise à jour

```bash
git pull
$COMPOSE up -d --build     # les migrations de base de données s'appliquent au démarrage du backend
```

## Sauvegardes

- Le service `db-backup` fait un `pg_dump` quotidien, chiffré en AES-256 (GPG), dans `data/backups/`,
  conservé 30 jours (`BACKUP_RETENTION_DAYS`).
- **Copie hors site** (recommandée : une panne de carte SD ou un vol emporterait tout) :
  1. Configurer un stockage avec rclone, de préférence hébergé en France ou dans l'UE (stockage
     objet S3, Nextcloud, etc.) :
     `docker run --rm -it -v $PWD/data/rclone:/config/rclone rclone/rclone config`
  2. Renseigner `RCLONE_DESTINATION=<remote>:<dossier>` dans `.env`.
  3. Activer : `$COMPOSE --profile horssite up -d`.

  Les fichiers envoyés sont déjà chiffrés : l'hébergeur ne peut pas les lire.

### Restaurer une sauvegarde

```bash
scripts/restaurer-sauvegarde.sh data/backups/presence_AAAAMMJJ_HHMMSS.dump.gpg
```

Testez une restauration au moins une fois (par exemple sur un autre Raspberry Pi) : une sauvegarde
jamais restaurée n'est pas une sauvegarde.

## Exploitation courante

| Besoin | Commande |
|---|---|
| Mot de passe de la pharmacienne oublié | `$COMPOSE exec backend flask reinitialiser-mdp pharmacienne` |
| Voir les journaux | `$COMPOSE logs -f backend nginx` |
| État des services | `$COMPOSE ps` |

Les arrivées, départs et mots de passe oubliés des employés se gèrent depuis l'écran **Employés**.

## Limiter l'accès au réseau de la pharmacie (optionnel)

Par défaut, l'application est accessible depuis Internet (les employés peuvent consulter leurs
informations de chez eux). Pour la réserver au réseau de la pharmacie, éditez `nginx/acces.conf`
(adresse IP publique de la box, puis `deny all;`) et redémarrez nginx : `$COMPOSE restart nginx`.

## RGPD

- Les motifs d'absence (dont « Maladie ») sont des données personnelles sensibles : seuls l'employé
  concerné et la pharmacienne y ont accès.
- Inscrire ce traitement au registre des traitements de la pharmacie (finalité : préparation de la
  paie ; durée de conservation alignée sur celle des éléments de paie).
- Les données des employés partis sont conservées (pas de suppression automatique).
