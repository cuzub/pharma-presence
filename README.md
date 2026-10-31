# Présences — Pharmacie

Application web de suivi des présences d'une équipe de pharmacie (~10 personnes), qui remplace
l'« état préparatoire » Excel envoyé chaque mois au comptable.

**Principe : l'outil enregistre les faits, le comptable interprète.** Aucun calcul de paie
(ni classement heures complémentaires / supplémentaires, ni décompte des congés, ni montant des
indemnités kilométriques). Voir [docs/intent/suivi-presence-pharmacie.md](docs/intent/suivi-presence-pharmacie.md).

## Fonctionnalités

**Pharmacienne (administratrice)**
- Tableau du mois : une ligne par employé, une colonne par jour ; clic sur une case pour saisir
  des heures en plus (au quart d'heure) ou une absence.
- Absences par période (premier jour d'absence → jour de reprise, ou « en cours ») avec motif ;
  les chevauchements sont refusés.
- Déplacements professionnels : saisis depuis le calendrier (clic sur la date, crayon pour
  modifier), avec des motifs prédéfinis dont les km se remplissent automatiquement (ou « Autre »,
  distance libre) ; validation des déplacements déclarés par les employés.
- Employés : arrivée (création du compte avec mot de passe provisoire), avenant, départ (compte
  désactivé, données conservées), retour, nouveau mot de passe provisoire.
- Export comptable mensuel : contrôles avant export (bloquant si des déplacements sont en attente),
  fichier Excel (Récapitulatif, Absences, Heures en plus, Déplacements) et CSV (format Excel FR).
- Paramètres : motifs d'absence, motifs de déplacement (destination + km), jours de fermeture.

**Employé**
- « Mon mois » : calendrier (absences et heures en plus en lecture seule) et résumé ; clic sur une
  date pour déclarer un déplacement, crayon pour le modifier tant qu'il n'est pas validé.

## Architecture

| Partie | Technologies |
|---|---|
| Backend | Flask 3, SQLAlchemy 2, Flask-Migrate (Alembic), Flask-JWT-Extended, PostgreSQL 16, openpyxl |
| Frontend | Vue 3, Vite, Pinia, Vue Router, axios, Bootstrap 5 |
| Déploiement | Docker Compose sur Raspberry Pi : nginx (HTTPS Let's Encrypt), gunicorn, sauvegardes chiffrées GPG, copie hors site rclone |

Sécurité : session JWT dans un cookie `HttpOnly; Secure; SameSite=Strict` (8 h) avec protection
CSRF, mot de passe provisoire à changer à la première connexion, sessions invalidées au changement
de mot de passe ou au départ, limitation des tentatives de connexion, cloisonnement des données par
employé vérifié par les tests. Contraintes PostgreSQL d'exclusion contre les chevauchements de
contrats et d'absences.

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
