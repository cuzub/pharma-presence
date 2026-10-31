# Suivi — Pharmacie

Application web de suivi d'une équipe de pharmacie (~10 personnes), qui remplace
l'« état préparatoire » Excel envoyé chaque mois au comptable.

**Principe : l'outil enregistre les faits, le comptable interprète.** Aucun calcul de paie
(ni classement heures complémentaires / supplémentaires, ni décompte des congés, ni montant des
indemnités kilométriques). Voir [docs/intent/suivi-presence-pharmacie.md](docs/intent/suivi-presence-pharmacie.md).

## Fonctionnalités

**Pharmacienne (administratrice)**
- Tableau du mois : une ligne par employé, une colonne par jour ; clic sur une case pour saisir
  des heures en plus / en moins (en minutes, par 5 : `15`, `-30`), une absence ou un déplacement.
- Tableau du mois : colonnes Employé, H +/- et Km figées, km du jour sous les minutes. H +/- = solde
  cumulé à la fin du mois affiché (tout l'historique, régularisations comprises).
- Régularisations d'heures +/- (Employés → Gérer) : crédit ou débit daté avec commentaire facultatif
  (heures payées, récupération, solde de départ, correction), affiché en violet dans le tableau et le
  calendrier de l'employé, compté dans le solde et les statistiques, absent de l'export.
- Absences par période (premier jour d'absence → jour de reprise, ou « en cours ») avec motif ;
  les chevauchements sont refusés. Un motif bloquant interdit les heures et déplacements les jours
  d'absence ; la suppression des saisies en conflit exige une confirmation.
- Déplacements professionnels : saisis depuis le Tableau du mois (clic sur la case du jour, crayon
  pour modifier), avec des motifs prédéfinis dont les km se remplissent automatiquement (ou « Autre »,
  distance libre). Déclaratifs : pas de validation, la pharmacienne peut tout corriger.
- Employés : arrivée (création du compte avec mot de passe provisoire), avenant, départ (compte
  désactivé, données conservées), retour, nouveau mot de passe provisoire.
- Export comptable mensuel : contrôles avant export, fichier Excel (Récapitulatif, Absences,
  Déplacements) et CSV (format Excel FR). Sans heures +/- ni entrées / sorties.
- Historique : journal immuable des créations / modifications / suppressions (déplacements, heures,
  régularisations, absences) avec auteur et avant → après, filtrable par employé, mois, auteur et type.
- Statistiques : heures en plus / en moins par année, en net, avec un graphique empilé par employé
  et mois, un tableau du net mensuel, les totaux annuels et d'équipe ; employés partis inclus.
  Clic sur un employé (légende ou tableau) pour l'isoler.
- Paramètres : motifs d'absence (avec l'option « Bloque heures et déplacements »), motifs de
  déplacement (destination + km), jours de fermeture.

**Employé**
- « Mon mois » : calendrier (absences et régularisations en lecture seule) et résumé (net du mois,
  solde cumulé) ; clic sur une date pour saisir
  ses heures +/- ou déclarer un déplacement, crayon pour le modifier ou le supprimer (mois en cours,
  et mois précédent jusqu'au 5 inclus).

## Architecture

| Partie | Technologies |
|---|---|
| Backend | Flask 3, SQLAlchemy 2, Flask-Migrate (Alembic), Flask-JWT-Extended, PostgreSQL 16, openpyxl |
| Frontend | Vue 3, Vite, Pinia, Vue Router, axios, Bootstrap 5 |
| Déploiement | Docker Compose sur Raspberry Pi : nginx (HTTPS Let's Encrypt), gunicorn, sauvegardes chiffrées GPG, copie hors site rclone |

Sécurité : session JWT dans un cookie `HttpOnly; Secure; SameSite=Strict` (8 h) avec protection
CSRF, mot de passe provisoire à changer à la première connexion, sessions invalidées à la
déconnexion, au changement de mot de passe ou au départ, limitation des tentatives de connexion
(5/min par adresse IP, 10 échecs par 15 min par identifiant, toutes IP confondues ; temps de
réponse identique pour un identifiant inconnu), politique CSP stricte servie par le conteneur
frontend, cloisonnement des données par employé vérifié par les tests. Contraintes PostgreSQL
d'exclusion contre les chevauchements de contrats et d'absences. Sauvegardes : en cas d'échec,
aucun fichier n'est écrit et une nouvelle tentative a lieu 5 minutes plus tard.

Recommandation : servir l'application sur son propre sous-domaine (ex. `pharmacie.pedalog.fr`)
plutôt que sous `app.pedalog.fr/pharmacie`. Sur une origine partagée, une faille dans Pedalog
donnerait accès aux données de la pharmacie (les chemins de cookies n'isolent pas deux applications
d'une même origine).

```
backend/          API Flask (app/routes, app/services, migrations/, tests/)
frontend/         Interface Vue (src/views/admin, src/views/employe, tests/unit, tests/e2e)
nginx/            Reverse proxy HTTPS de production
deploy/compose/   docker-compose.dev.yml (PostgreSQL de dev) et docker-compose.yml (production)
scripts/          Certificat HTTPS, restauration de sauvegarde
docs/             Déploiement, guide d'utilisation, intention validée
```

## Développement

Pré-requis : Docker, Python 3.13+, Node 24+.

```bash
# PostgreSQL de développement (port 5433) avec la base de test « presence_test »
docker compose -f deploy/compose/docker-compose.dev.yml up -d

# Backend (port 5002)
cd backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
FLASK_APP=run.py .venv/bin/flask db upgrade
FLASK_APP=run.py FLASK_ENV=development .venv/bin/flask demo   # données FICTIVES : admin / admin-demo-1234
FLASK_ENV=development PORT=5002 .venv/bin/python run.py

# Frontend (port 5174, proxy /api → 5002)
cd frontend
npm install
npm run dev
```

## Tests

```bash
cd backend && .venv/bin/python -m pytest      # API, cloisonnement, contraintes, export (base presence_test)
cd frontend && npm run test:unit              # jours fériés, calendrier, garde du routeur
cd frontend && npm run test:e2e               # parcours complet (serveurs de dev + `flask demo`)
```

Après une modification des modèles : `FLASK_APP=run.py .venv/bin/flask db migrate -m "description"`,
relire la migration générée, puis `flask db upgrade`.

## Production

Voir [docs/deploiement.md](docs/deploiement.md) et le [guide d'utilisation](docs/guide-utilisation.md).
