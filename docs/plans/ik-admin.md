# Plan d'implémentation : indemnités kilométriques (IK) des admins

Intention validée : [../intent/ik-admin.md](../intent/ik-admin.md). Lire ce document en premier.

Ce plan est écrit pour être exécuté **tâche par tâche, dans l'ordre**. Chaque tâche indique les
fichiers à toucher, le code attendu et la vérification à lancer avant de passer à la suivante.
Ne pas improviser hors de ce périmètre ; en cas de doute, s'arrêter et demander.

---

## 0. Décisions techniques (déjà tranchées)

| Sujet | Décision |
|---|---|
| Rattachement d'un déplacement admin | `deplacements.employe_id` devient **nullable** ; nouvelle colonne `deplacements.utilisateur_id` (FK `utilisateurs.id`). Contrainte : exactement l'un des deux est renseigné. **Aucune fausse fiche `Employe`.** |
| Nom affiché de la ligne admin | Nouvelle colonne `utilisateurs.nom_affiche` (facultative). Libellé = `nom_affiche` sinon `identifiant`. Modifiable par l'admin connecté dans *Paramètres* → carte « Indemnités kilométriques ». |
| Coefficient IK | Nouvelle table singleton `parametres_ik` (id = 1), colonne `coefficient` `Numeric(6, 3)` **nullable** (NULL = pas encore renseigné). Bornes : > 0 et ≤ 10, 3 décimales max. |
| Données du tableau | `GET /api/mois/<mois>` renvoie une nouvelle clé `admins` (liste séparée de `employes`). Pour un employé connecté : `admins: []`. Ainsi l'aperçu de la vue *Export* (qui lit `employes`) ne change pas. |
| Saisie | `POST /api/deplacements` accepte `utilisateur_id` (admin uniquement), qui **doit** être l'id de l'admin connecté, sinon 403. PUT/DELETE d'un déplacement d'un autre admin : 403. Pas de fenêtre de saisie, pas de contrôle de contrat ni d'absence pour une ligne admin. Un seul déplacement par jour et par admin. |
| Historique | Nouvelle colonne `journal_modifications.admin_concerne_id` (FK SET NULL). `to_dict` expose `admin_concerne_nom`. Affiché dans la colonne « Employé concerné » sous la forme « Elise (IK) ». Pas de nouveau filtre. |
| Export IK | `GET /api/exports/ik/<annee>.xlsx` (admin). Déplacements **de l'admin connecté** uniquement. Refus 409 si le coefficient n'est pas renseigné. Nom du fichier : `indemnites-km-<annee>.xlsx`. |
| Montants | Calcul en `Decimal` : montant du mois = `km_mois × coefficient`, arrondi au centime (ROUND_HALF_UP). Total montant = somme des montants mensuels arrondis. |
| Statistiques, solde, État préparatoire, CSV | Inchangés : ils ne doivent **jamais** inclure les déplacements admin (vérifié par des tests). |

---

## 1. Base de données et modèles

### Tâche 1.1 : modèles (`backend/app/models.py`)

1. Classe `Utilisateur` :
   - ajouter `nom_affiche = db.Column(db.String(100), nullable=True)` ;
   - ajouter la propriété :
     ```python
     @property
     def libelle(self):
         """Nom affiché sur la ligne IK de l'admin (à défaut : l'identifiant)."""
         return self.nom_affiche or self.identifiant
     ```
   - dans `to_dict()`, ajouter `'nom_affiche': self.nom_affiche,`.
2. Classe `Deplacement` :
   - `employe_id` : passer `nullable=False` → `nullable=True` (garder la FK, `ondelete='CASCADE'` et l'index) ;
   - ajouter
     `utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateurs.id', ondelete='CASCADE'), nullable=True, index=True)` ;
   - ajouter `utilisateur = db.relationship('Utilisateur', foreign_keys=[utilisateur_id])`
     (**`foreign_keys` obligatoire** : `Horodatage.updated_by_id` pointe aussi vers `utilisateurs`) ;
   - dans `__table_args__`, ajouter
     `db.CheckConstraint('(employe_id IS NULL) <> (utilisateur_id IS NULL)', name='ck_deplacements_titulaire'),` ;
   - dans `to_dict()`, ajouter `'utilisateur_id': self.utilisateur_id,`.
3. Classe `JournalModification` :
   - ajouter `admin_concerne_id = db.Column(db.Integer, db.ForeignKey('utilisateurs.id', ondelete='SET NULL'), nullable=True)` ;
   - ajouter `admin_concerne = db.relationship('Utilisateur', foreign_keys=[admin_concerne_id])` ;
   - dans `to_dict()`, ajouter `'admin_concerne_nom': self.admin_concerne.libelle if self.admin_concerne else None,`.
4. Nouvelle classe, à la fin du fichier, sur le modèle de `ParametresMail` :
   ```python
   class ParametresIK(Horodatage, db.Model):
       """Coefficient des indemnités kilométriques (€/km). Table à une seule ligne (id = 1)."""

       __tablename__ = 'parametres_ik'

       id = db.Column(db.Integer, primary_key=True)
       coefficient = db.Column(db.Numeric(6, 3), nullable=True)

       __table_args__ = (db.CheckConstraint('id = 1', name='ck_parametres_ik_singleton'),)

       def to_dict(self):
           return {'coefficient': float(self.coefficient) if self.coefficient is not None else None}
   ```

### Tâche 1.2 : migration `backend/migrations/versions/0007_ik_admin.py`

Écrire la migration **à la main**, en reprenant l'en-tête de `0006_parametres_mail.py` :
`revision = '0007'`, `down_revision = '0006'`, docstring « Indemnités kilométriques des admins ».

`upgrade()` :
```python
op.add_column('utilisateurs', sa.Column('nom_affiche', sa.String(100), nullable=True))

op.alter_column('deplacements', 'employe_id', existing_type=sa.Integer(), nullable=True)
op.add_column('deplacements', sa.Column('utilisateur_id', sa.Integer(), nullable=True))
op.create_foreign_key('fk_deplacements_utilisateur', 'deplacements', 'utilisateurs', ['utilisateur_id'], ['id'], ondelete='CASCADE')
op.create_index('ix_deplacements_utilisateur_id', 'deplacements', ['utilisateur_id'])
op.create_check_constraint('ck_deplacements_titulaire', 'deplacements', '(employe_id IS NULL) <> (utilisateur_id IS NULL)')

op.add_column('journal_modifications', sa.Column('admin_concerne_id', sa.Integer(), nullable=True))
op.create_foreign_key('fk_journal_admin_concerne', 'journal_modifications', 'utilisateurs', ['admin_concerne_id'], ['id'], ondelete='SET NULL')

op.create_table(
    'parametres_ik',
    sa.Column('id', sa.Integer(), primary_key=True),
    sa.Column('coefficient', sa.Numeric(6, 3), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_by_id', sa.Integer(), sa.ForeignKey('utilisateurs.id', ondelete='SET NULL'), nullable=True),
    sa.CheckConstraint('id = 1', name='ck_parametres_ik_singleton'),
)
```

`downgrade()` (ordre inverse) :
```python
op.drop_table('parametres_ik')
op.drop_constraint('fk_journal_admin_concerne', 'journal_modifications', type_='foreignkey')
op.drop_column('journal_modifications', 'admin_concerne_id')
op.execute('DELETE FROM deplacements WHERE utilisateur_id IS NOT NULL')
op.drop_constraint('ck_deplacements_titulaire', 'deplacements', type_='check')
op.drop_index('ix_deplacements_utilisateur_id', table_name='deplacements')
op.drop_constraint('fk_deplacements_utilisateur', 'deplacements', type_='foreignkey')
op.drop_column('deplacements', 'utilisateur_id')
op.alter_column('deplacements', 'employe_id', existing_type=sa.Integer(), nullable=False)
op.drop_column('utilisateurs', 'nom_affiche')
```

### Tâche 1.3 : nettoyage des tests (`backend/tests/conftest.py`)

Dans `_TABLES`, ajouter `'parametres_ik'` **en tête de liste**.

**Vérification** : `cd backend && .venv/bin/python -m pytest` → tout passe. La fixture `app`
fait `downgrade base` puis `upgrade`, ce qui teste la migration dans les deux sens.

---

## 2. Paramètres IK (API)

### Tâche 2.1 : routes (`backend/app/routes/parametres.py`)

Ajouter, sur le modèle de `/mail` :

- `GET /api/parametres/ik` (`@admin_requis`) → `{'coefficient': <float|None>, 'nom_affiche': current_user.nom_affiche or ''}`.
- `PUT /api/parametres/ik` (`@admin_requis`), corps `{coefficient, nom_affiche}` :
  - `coefficient` : obligatoire. Utiliser `parse_decimal(data.get('coefficient'), 'coefficient')`
    (accepte `"0,636"` et `0.636`, refuse ≤ 0). Refuser ensuite si `> 10`
    (`ApiError('Coefficient IK trop élevé (10 €/km maximum)')`) ou si
    `coefficient.as_tuple().exponent < -3` (`ApiError('Coefficient IK : 3 décimales maximum')`).
  - `nom_affiche` : `texte(data, 'nom_affiche', obligatoire=False, longueur_max=100)`, affecté à
    `current_user.nom_affiche` (None si vide).
  - Créer la ligne `ParametresIK(id=1)` si elle est absente, `updated_by_id = current_user.id`, commit.
  - Réponse 200 : même format que le GET.
- Importer `ParametresIK`, `parse_decimal` et `current_user` (`from flask_jwt_extended import current_user`).

### Tâche 2.2 : tests `backend/tests/test_parametres_ik.py`

- GET par défaut → `{'coefficient': None, 'nom_affiche': ''}`.
- PUT `{'coefficient': '0,636', 'nom_affiche': 'Elise'}` → 200 ; la relecture donne `coefficient == 0.636`
  et `nom_affiche == 'Elise'` ; `GET /api/auth/me` contient `nom_affiche == 'Elise'`.
- Refus 400 : `0`, `-1`, `'abc'`, `10.5`, `'0,6361'`, coefficient absent.
- Employé (fixture `creer_employe`) → 403 sur le GET et le PUT.

**Vérification** : `.venv/bin/python -m pytest tests/test_parametres_ik.py tests/test_auth.py`.

---

## 3. Déplacements des admins (API)

### Tâche 3.1 : journal (`backend/app/services/journal.py`)

Ajouter un paramètre nommé à `journaliser` :
```python
def journaliser(type_, action, employe_id, objet_id, avant=None, apres=None, admin_concerne_id=None):
```
et le transmettre au constructeur : `JournalModification(..., admin_concerne_id=admin_concerne_id)`.
Les appels existants ne changent pas.

### Tâche 3.2 : routes (`backend/app/routes/deplacements.py`)

1. `_get(deplacement_id)` : après la recherche existante, ajouter
   ```python
   if deplacement.utilisateur_id is not None and deplacement.utilisateur_id != current_user.id:
       raise ApiError('Vous ne pouvez modifier que vos propres déplacements', 403, 'acces_refuse')
   ```
   Un employé ne peut pas atteindre ce cas : la condition existante renvoie déjà 404, car
   `employe_id` vaut None.
2. `_remplir(deplacement, data)` : remplacer
   ```python
   verifier_jour_saisissable(db.session.get(Employe, deplacement.employe_id), deplacement.date)
   ```
   par
   ```python
   if deplacement.employe_id is not None:
       verifier_jour_saisissable(db.session.get(Employe, deplacement.employe_id), deplacement.date)
   ```
   `_verifier_fenetre` n'est appelé que pour un non-admin : rien à changer.
3. `_verifier_unicite_du_jour` : filtrer selon le titulaire.
   ```python
   if deplacement.utilisateur_id is not None:
       autres = Deplacement.query.filter(Deplacement.utilisateur_id == deplacement.utilisateur_id, Deplacement.date == deplacement.date)
       message = 'Un déplacement est déjà enregistré ce jour-là'
   else:
       autres = Deplacement.query.filter(Deplacement.employe_id == deplacement.employe_id, Deplacement.date == deplacement.date)
       message = 'Un déplacement est déjà enregistré ce jour-là pour cet employé'
   ```
   Garder le filtre `Deplacement.id != deplacement.id` et lever `ApiError(message, 409)`.
4. `creer()` : côté admin, remplacer le bloc `employe_id` par :
   ```python
   if current_user.est_admin:
       utilisateur_id = data.get('utilisateur_id')
       if utilisateur_id is not None:
           if utilisateur_id != current_user.id:
               raise ApiError('Vous ne pouvez saisir que vos propres déplacements', 403, 'acces_refuse')
           deplacement.utilisateur_id = current_user.id
       else:
           employe_id = data.get('employe_id')
           if not isinstance(employe_id, int) or db.session.get(Employe, employe_id) is None:
               raise ApiError('Employé introuvable')
           deplacement.employe_id = employe_id
   else:
       deplacement.employe_id = employe_courant_id()   # utilisateur_id envoyé par un employé : ignoré
   ```
5. Les 3 appels à `journaliser(...)` (création, modification, suppression) : ajouter
   `admin_concerne_id=deplacement.utilisateur_id`.
6. `lister()` : ne rien changer (le `join(Employe)` exclut déjà les déplacements admin). Ajouter
   un commentaire d'une ligne : `# Jointure interne : les déplacements des admins (IK) sont exclus.`

### Tâche 3.3 : données du mois (`backend/app/services/mois.py`)

1. Dans `donnees_mois`, rendre l'exclusion explicite :
   `deplacements_q = Deplacement.query.filter(Deplacement.employe_id.isnot(None), Deplacement.date.between(debut, fin))`.
   Ainsi l'État préparatoire, le CSV, les contrôles et les lignes employés du tableau ne voient
   jamais les déplacements admin.
2. Nouvelle fonction (ajouter `Utilisateur` à l'import de `app.models`) :
   ```python
   def lignes_admins(debut, fin, utilisateur_courant):
       """Lignes IK du tableau du mois : admins actifs, et admins désactivés ayant des déplacements ce mois-ci."""
       deplacements = defaultdict(list)
       for d in (Deplacement.query.filter(Deplacement.utilisateur_id.isnot(None), Deplacement.date.between(debut, fin))
                 .order_by(Deplacement.date).all()):
           deplacements[d.utilisateur_id].append(d)
       admins = Utilisateur.query.filter(Utilisateur.role == Utilisateur.ROLE_ADMIN).all()
       admins = [a for a in admins if a.actif or a.id in deplacements]
       admins.sort(key=lambda a: a.libelle.lower())
       return [{
           'id': a.id,
           'nom': a.libelle,
           'est_moi': a.id == utilisateur_courant.id,
           'deplacements': [d.to_dict() for d in deplacements[a.id]],
           'total_km': sum(float(d.km) for d in deplacements[a.id]),
       } for a in admins]
   ```
3. `serialiser_mois(debut, fin, lignes, admins=None)` : ajouter `'admins': admins or []` au dict renvoyé.

### Tâche 3.4 : route du mois (`backend/app/routes/mois.py`)

Dans `mois_detail` :
```python
admins = lignes_admins(debut, fin, current_user) if current_user.est_admin else []
return jsonify(serialiser_mois(debut, fin, lignes, admins)), 200
```

### Tâche 3.5 : tests `backend/tests/test_ik_admin.py` (partie saisie)

Fixture locale `autre_admin(app)` : crée un `Utilisateur(identifiant='associe', role=Utilisateur.ROLE_ADMIN)`
avec `definir_mot_de_passe(ADMIN_MDP, provisoire=False)`, commit, et renvoie une `Session` connectée
(copier la fixture `admin` de `conftest.py`, importer `ADMIN_MDP` et `Session` depuis `tests.conftest`).
Récupérer l'id de l'admin courant avec `admin.get('/api/auth/me').get_json()['id']`.

Cas à couvrir :
1. L'admin crée `{'utilisateur_id': moi, 'date': '2025-02-12', 'motif': 'Banque', 'km': 12}` → 201,
   **sans aucun employé ni contrat**. `GET /api/mois/2025-02` → `admins` contient une ligne avec
   `est_moi: True` et `total_km == 12`, et `employes == []`.
2. Un second déplacement le même jour → 409.
3. `utilisateur_id` d'un autre admin → 403. PUT et DELETE d'un déplacement de `autre_admin` par
   `admin` → 403. `autre_admin` voit la ligne de `admin` dans `admins` avec `est_moi: False`.
4. Un employé qui envoie `utilisateur_id` → le déplacement est créé à **son** nom (`employe_id`
   renseigné, `utilisateur_id` None). `GET /api/mois/...` côté employé → `admins == []`.
   PUT/DELETE d'un déplacement admin par un employé → 404.
5. Admin désactivé (`actif=False` en base) sans déplacement : absent de `admins`. Avec un
   déplacement dans le mois : présent.
6. Journal : après une création, `GET /api/journal` → ligne avec `type == 'deplacement'`,
   `employe_id is None` et `admin_concerne_nom == 'pharmacienne'`, puis `'Elise'` après un PUT
   `/api/parametres/ik` avec `nom_affiche`.
7. Exclusion de l'État préparatoire : un employé avec un déplacement de 22 km et l'admin avec un
   déplacement de 30 km en février 2025. Dans l'Excel `etat-preparatoire.xlsx`, l'onglet
   *Déplacements* contient **une seule** ligne (22 km) et le *Récapitulatif* ne contient pas
   l'admin. `GET /api/exports/2025-02/controles` ne mentionne pas l'admin, `recap.csv` non plus.
8. `GET /api/deplacements` (admin, sans filtre) ne renvoie pas le déplacement admin.
9. `GET /api/statistiques/2025` : réponse identique avant et après la création d'un déplacement admin.

**Vérification** : `.venv/bin/python -m pytest` (toute la suite : les tests existants des
déplacements, de l'export et du cloisonnement doivent rester verts).

---

## 4. Export IK (API)

### Tâche 4.1 : service (`backend/app/services/export.py`)

Imports à ajouter : `from datetime import date, datetime`, `from decimal import Decimal, ROUND_HALF_UP`,
`from app.models import Deplacement`, et `MOIS_FR` dans l'import existant de `app.services.mois`.

```python
_CENTIME = Decimal('0.01')


def km_par_mois(utilisateur_id, annee):
    """Somme des km de l'admin pour chaque mois de l'année (liste de 12 Decimal)."""
    totaux = [Decimal('0')] * 12
    deplacements = Deplacement.query.filter(
        Deplacement.utilisateur_id == utilisateur_id,
        Deplacement.date.between(date(annee, 1, 1), date(annee, 12, 31)),
    ).all()
    for d in deplacements:
        totaux[d.date.month - 1] += d.km
    return totaux


def _format_coefficient(coefficient):
    return f'{coefficient:.3f}'.rstrip('0').rstrip('.').replace('.', ',')


def generer_excel_ik(utilisateur, annee, coefficient):
    km = km_par_mois(utilisateur.id, annee)
    montants = [(k * coefficient).quantize(_CENTIME, rounding=ROUND_HALF_UP) for k in km]
    wb = Workbook()
    ws = _feuille(wb, f'IK {annee}', f'Indemnités kilométriques — {utilisateur.libelle} — {annee}',
                  ['Mois', 'Kilomètres', 'Montant (€)'], premiere=True)
    ws['A3'] = f'Coefficient IK : {_format_coefficient(coefficient)} €/km'  # ligne 3 laissée vide par _feuille
    ws.freeze_panes = 'A5'
    for index in range(12):
        ws.append([f'{MOIS_FR[index].capitalize()} {annee}', float(km[index]), float(montants[index])])
    ws.append(['Total', float(sum(km)), float(sum(montants))])
    for cellule in ws[ws.max_row]:
        cellule.font = Font(bold=True)
    for ligne in ws.iter_rows(min_row=5, max_row=ws.max_row):
        ligne[1].number_format = '0.0'
        ligne[2].number_format = '#,##0.00 €'
    _largeurs(ws, [20, 14, 16])
    _neutraliser_formules(wb)
    flux = io.BytesIO()
    wb.save(flux)
    return flux.getvalue()
```
Ne pas utiliser `format_nombre_fr` pour le coefficient : il arrondit à 2 décimales (0,636 → 0,64).

### Tâche 4.2 : route (`backend/app/routes/mois.py`)

```python
@mois_bp.route('/exports/ik/<int:annee>.xlsx', methods=['GET'])
@admin_requis
def export_ik(annee):
    if not 2000 <= annee <= 2100:
        raise ApiError('Année invalide')
    parametres = db.session.get(ParametresIK, 1)
    if parametres is None or parametres.coefficient is None:
        raise ApiError("Renseignez le coefficient IK dans Paramètres avant d'exporter", 409, 'coefficient_ik_manquant')
    contenu = generer_excel_ik(current_user, annee, parametres.coefficient)
    return _fichier(contenu, f'indemnites-km-{annee}.xlsx', _XLSX)
```
Imports : `from app.extensions import db`, `from app.models import ParametresIK`, `generer_excel_ik`.
Déclarer cette route **avant** les routes `/exports/<mois>/...` n'est pas nécessaire (motifs différents),
mais vérifier que `/api/exports/ik/2025.xlsx` ne tombe pas sur `export_controles`.

### Tâche 4.3 : tests (suite de `backend/tests/test_ik_admin.py`)

1. Sans coefficient → 409, `code == 'coefficient_ik_manquant'`.
2. Coefficient `0,636`. Déplacements de l'admin : 31/12/2024 (10 km, à exclure), 01/01/2025
   (30 km), 15/01/2025 (2 km), 12/03/2025 (5,5 km), 31/12/2025 (1 km). Déplacements d'un
   employé (100 km) et d'un autre admin (50 km) en 2025 : à exclure.
   `GET /api/exports/ik/2025.xlsx` → 200, `indemnites-km-2025.xlsx` dans `Content-Disposition`.
   Avec `load_workbook(io.BytesIO(reponse.data))` :
   - `wb.sheetnames == ['IK 2025']` ;
   - `A1 == 'Indemnités kilométriques — pharmacienne — 2025'` ; `A3` contient `0,636` ;
   - ligne 4 : `['Mois', 'Kilomètres', 'Montant (€)']` ;
   - lignes 5 à 16 : `Janvier 2025` → `Décembre 2025` ; janvier `32.0` km / `20.35` € ;
     février `0.0` / `0.0` ; mars `5.5` / `3.5` (5,5 × 0,636 = 3,498 → 3,50) ;
     décembre `1.0` / `0.64` ;
   - ligne 17 : `['Total', 38.5, 24.49]` (20,35 + 3,50 + 0,64).
   Comparer les montants avec `pytest.approx`.
3. `GET /api/exports/ik/1999.xlsx` → 400. Employé → 403.

**Vérification** : `.venv/bin/python -m pytest`.

---

## 5. CLI et données de démonstration (`backend/app/cli.py`)

1. `creer-admin` : ajouter l'option `@click.option('--nom', default=None, help='Nom affiché (ex : Elise)')`
   → `admin.nom_affiche = nom.strip() if nom else None`.
2. `_creer_demo()` : `admin.nom_affiche = 'Elise'`. Après la boucle des employés, faire un
   `db.session.flush()` (pour que `admin.id` existe) puis ajouter une dizaine de déplacements admin
   sur les deux ans (boucle sur les jours, `hasard.random() < 0.03`, jours hors dimanche, motif tiré
   dans `destinations`, `utilisateur_id=admin.id`, `motif=destination.libelle`, `km=destination.km`).
3. Dans `_TABLES_DEMO`, ajouter `'parametres_ik'` en tête.

**Vérification** : `cd backend && FLASK_APP=run.py .venv/bin/flask demo --reinitialiser`, puis
`.venv/bin/python -m pytest`.

---

## 6. Frontend

Conventions : Vue 3 `<script setup>`, Bootstrap 5, icônes `bi-*`, textes en français, infobulles
via `v-infobulle`. Toujours passer par `api`, `telecharger` et `messageErreur` de `src/services/api.js`.

### Tâche 6.1 : boîte de saisie (`frontend/src/components/JourModal.vue`)

Ajouter la prop `ligneAdmin: { type: Boolean, default: false }`
(commentaire : `// Ligne IK d'un admin : déplacement seul, ni heures, ni contrat, ni absence.`).

- Masquer avec `v-if="!ligneAdmin"` : le titre « Heures en plus / en moins », les 4 alertes de
  blocage (`horsContrat`, `absenceBloquante`, `verrouilleEmploye`, `blocageEmploye`), tout le bloc
  des heures (du `<h6 v-if="vueEmploye" ...>Heures +/-` jusqu'au `<p class="form-text">… Ex. : 15 = …</p>` inclus)
  et le bloc des régularisations.
- `horsContrat` : renvoyer `false` si `props.ligneAdmin`.
- `titre` : si `props.ligneAdmin` → `` `${props.employe.nom} — Déplacement — ${formatFr(props.jour)}` ``.
- Le `watch` d'ouverture : ne pas focaliser `champHeures` si `ligneAdmin` (le champ n'existe pas).
- `enregistrerDeplacement` : remplacer la ligne `...(props.vueEmploye ? {} : { employe_id: props.employe.id })` par
  ```js
  ...(props.ligneAdmin ? { utilisateur_id: props.employe.id } : props.vueEmploye ? {} : { employe_id: props.employe.id })
  ```
- `enregistrer` : ne pas appeler `sauverHeures` si `props.ligneAdmin`.

### Tâche 6.2 : tableau du mois (`frontend/src/views/admin/TableauMois.vue`)

1. Dans `<tbody>`, **après** la boucle des employés, ajouter :
   - une ligne de séparation (seulement si `donnees.admins?.length`) :
     `<tr class="separateur-ik"><th class="col-employe" scope="row">Déplacements des admins (IK)</th><td :colspan="jours.length + 2"></td></tr>` ;
   - une boucle `v-for="admin in donnees.admins" :key="'admin-' + admin.id"` contenant :
     - la cellule nom : `{{ admin.nom }}` + une petite ligne `small text-muted` : « Mes déplacements (IK) »
       si `admin.est_moi`, sinon « Lecture seule » ;
     - pour chaque jour, deux variantes de `td` :
       - `v-if="admin.est_moi"` : classes `['case', jour.classes]`, `role="button"`, `tabindex="0"`,
         `data-admin`, `:data-jour="jour.iso"`, `@click` et `@keydown.enter` → `ouvrirAdmin(admin, jour.iso)` ;
       - `v-else` : classes `['case', 'lecture-seule', jour.classes]`, sans clic ;
       - contenu identique : `<div v-if="kmDuJour(admin, jour.iso)" class="km-jour">{{ formatNombre(kmDuJour(admin, jour.iso)) }} km</div>` ;
       - infobulle : `titreCaseAdmin(admin, jour)`, avec
         ```js
         const titreCaseAdmin = (admin, jour) => {
           const deplacements = deplacementsDuJour(admin, jour.iso)
           return [admin.nom, ...jour.lignes, ...deplacements.map((d) => `• ${d.motif} — ${formatNombre(d.km)} km`)]
         }
         ```
     - la cellule H +/- vide : `<td class="col-total col-hpm"></td>` ;
     - la cellule Km : `<td class="col-total col-km" v-infobulle="titreKm(admin)">{{ admin.total_km ? formatNombre(admin.total_km) : '' }}</td>`
       (`titreKm`, `kmDuJour` et `deplacementsDuJour` existants fonctionnent tels quels).
2. L'état « Aucun employé sous contrat » reste affiché si `employes` est vide ; les lignes admin
   s'affichent quand même en dessous.
3. État de saisie admin **séparé** de `useSaisieJour` (les ids admin sont des ids d'utilisateur et
   peuvent coïncider avec des ids d'employé). Importer `reactive` depuis `vue`.
   ```js
   const saisieAdmin = reactive({ ouvert: false, adminId: null, jour: '' })
   const ouvrirAdmin = (admin, jour) => Object.assign(saisieAdmin, { ouvert: true, adminId: admin.id, jour })
   const ligneAdminModal = computed(() => {
     const admin = donnees.value.admins.find((a) => a.id === saisieAdmin.adminId)
     return admin ? { ...admin, prenom: '', contrats: [], absences: [], heures: {}, regularisations: [] } : null
   })
   const apresSaisieAdmin = async () => {
     saisieAdmin.ouvert = false
     await charger()
   }
   ```
   et, sous le `JourModal` existant :
   ```html
   <JourModal
     ligne-admin
     :ouvert="saisieAdmin.ouvert"
     :employe="ligneAdminModal"
     :jour="saisieAdmin.jour"
     @fermer="saisieAdmin.ouvert = false"
     @modifie="apresSaisieAdmin"
   />
   ```
4. Valeur initiale de `donnees` : `ref({ employes: [], admins: [], jours_fermeture: [] })`.
5. CSS (scoped) :
   ```css
   .separateur-ik th,
   .separateur-ik td {
     font-size: 0.7rem;
     text-transform: uppercase;
     color: #6c757d;
     background: #f8f9fa;
   }

   .case.lecture-seule {
     cursor: default;
   }

   .case.lecture-seule:hover {
     outline: none;
   }
   ```
6. Légende : ajouter `<span class="text-muted">Dernières lignes : déplacements des admins (IK), hors État préparatoire.</span>`.

### Tâche 6.3 : paramètres (`frontend/src/views/admin/Parametres.vue`)

1. Nouvelle carte « Indemnités kilométriques » (5ᵉ carte, même structure que « Envoi de l'export
   par mail ») : elle affiche *Coefficient* (`0,636 €/km`, ou « Non renseigné » en `text-danger`)
   et *Nom sur ma ligne* (`nom_affiche`, ou « Identifiant par défaut »). Bouton crayon :
   `ouvrir('ik')`, `aria-label` et infobulle « Modifier le coefficient IK et le nom affiché ».
2. Nouvelle `Modal` avec `ouvert === 'ik'` et le titre « Indemnités kilométriques » :
   - texte d'aide : « Le coefficient (€/km) multiplie les kilomètres de chaque mois dans l'export
     *Télécharger mes IK* (menu Export). Il s'applique à toute l'année exportée. Le nom s'affiche
     sur votre ligne du Tableau du mois. » ;
   - alerte d'erreur comme dans les autres modales ;
   - champ `ik-coefficient` (libellé « Coefficient IK (€/km) ») : `type="text" inputmode="decimal"`,
     placeholder `0,636`, `required` ;
   - champ `ik-nom` (libellé « Nom sur ma ligne ») : `maxlength="100"`, placeholder « ex : Elise » ;
   - bouton *Enregistrer* + « Enregistré » en vert, comme pour le mail.
3. Script :
   - `const ik = reactive({ coefficient: '', nom_affiche: '' })`, `const ikEnregistre = ref(false)` ;
   - `chargerIk()` : GET `/parametres/ik` ; `ik.coefficient = data.coefficient == null ? '' : String(data.coefficient).replace('.', ',')` ;
     `ik.nom_affiche = data.nom_affiche` ;
   - `enregistrerIk()` : PUT `/parametres/ik` avec `{ coefficient: ik.coefficient, nom_affiche: ik.nom_affiche }`,
     relire la réponse comme dans `chargerIk`, `ikEnregistre.value = true`, puis
     `useAuthStore().chargerSession()` pour mettre à jour le nom dans l'en-tête ;
   - appeler `chargerIk()` dans `onMounted` ; remettre `ikEnregistre.value = false` dans `ouvrir()`.
   - Carte : afficher le coefficient avec `formatCoefficient = (c) => (c ? `${c} €/km` : '')` sur `ik.coefficient`.

### Tâche 6.4 : export (`frontend/src/views/admin/Export.vue`)

Sous le bloc des boutons existants (`<div class="mt-3">…</div>`), ajouter une carte :
```html
<div class="carte mt-4">
  <h2 class="h6">Indemnités kilométriques (IK)</h2>
  <p class="small text-muted mb-2">
    Vos déplacements de l'année, mois par mois, avec le montant (km × coefficient IK).
    À envoyer une fois par an au comptable. Ils ne figurent pas dans l'État préparatoire.
  </p>
  <div class="d-flex flex-wrap align-items-end gap-2">
    <div>
      <label for="ik-annee" class="form-label small mb-1">Année</label>
      <select id="ik-annee" v-model.number="anneeIk" class="form-select form-select-sm">
        <option v-for="a in anneesIk" :key="a" :value="a">{{ a }}</option>
      </select>
    </div>
    <button type="button" class="btn btn-outline-primary" @click="exporterIk">
      <i class="bi bi-file-earmark-excel"></i> Télécharger mes IK
    </button>
  </div>
</div>
```
Script : ajouter `anneeCourante` à l'import de `../../utils/dates`, puis
```js
const anneeIk = ref(anneeCourante())
const anneesIk = Array.from({ length: 6 }, (_, i) => anneeCourante() - i)

const exporterIk = async () => {
  erreur.value = ''
  try {
    await telecharger(`/exports/ik/${anneeIk.value}.xlsx`, `indemnites-km-${anneeIk.value}.xlsx`)
  } catch (error) {
    erreur.value = await messageErreur(error, 'Export IK impossible')
  }
}
```
`messageErreur` sait déjà lire un message JSON dans une réponse `Blob` : le 409 « Renseignez le
coefficient IK… » s'affichera tel quel.

### Tâche 6.5 : historique (`frontend/src/views/admin/Historique.vue`)

Cellule « Employé concerné » :
```html
<td class="text-nowrap">{{ l.employe_nom ? `${l.employe_nom} ${l.employe_prenom}` : l.admin_concerne_nom ? `${l.admin_concerne_nom} (IK)` : '—' }}</td>
```

### Tâche 6.6 : en-tête (`frontend/src/stores/auth.js`)

Dans `nomAffiche` : `return u.prenom ? `${u.prenom} ${u.nom}` : (u.nom_affiche || u.identifiant)`.

**Vérification frontend** :
```bash
cd frontend && npm run test:unit && npm run build
```
Puis vérification manuelle (serveurs de dev, `flask demo --reinitialiser`, connexion `admin` / `admin-demo-1234`) :
1. *Paramètres* → carte IK : saisir `0,636` et `Elise` → l'en-tête affiche « Elise ».
2. *Tableau* : la ligne « Elise » est en dernier, sous le séparateur. Un clic ouvre une boîte
   **sans** heures +/-. Après l'enregistrement d'un déplacement, les km s'affichent dans la case
   et dans la colonne Km.
3. *Export* : l'aperçu et l'État préparatoire du mois ne contiennent pas Elise.
   *Télécharger mes IK* pour l'année en cours → l'Excel a 12 mois, les montants et la ligne Total.
4. Coefficient vidé en base (`UPDATE parametres_ik SET coefficient = NULL`) → message d'erreur
   clair dans *Export*.
5. *Historique* : le déplacement apparaît avec « Elise (IK) ».
6. *Statistiques* : inchangées.
7. Connexion employé (`alice` / `employe-demo-1234`) : *Mon mois* ne montre aucune ligne admin.

---

## 7. Documentation

1. `README.md` → *Fonctionnalités / Pharmacienne* : nouvelle puce « Indemnités kilométriques :
   chaque admin a sa ligne (en dernier) dans le Tableau du mois pour ses propres déplacements
   (hors État préparatoire) ; export Excel annuel « Télécharger mes IK » (km et montant par mois,
   totaux) ; coefficient IK dans Paramètres. » Compléter la puce *Paramètres* avec « coefficient IK ».
2. `docs/guide-utilisation.md` → nouvelle section `### Vos indemnités kilométriques (IK)`, juste
   avant `### En fin de mois : l'export pour le comptable`. Y expliquer :
   - la saisie sur votre ligne en bas du tableau ;
   - les lignes des autres admins, en lecture seule ;
   - le réglage du coefficient et du nom dans *Paramètres* ;
   - l'export une fois par an depuis *Export*, en choisissant l'année ;
   - l'absence de ces déplacements dans l'État préparatoire.

   Dans la section sur l'export, préciser aussi que les déplacements des admins n'y figurent pas.
3. `docs/deploiement.md` : la commande `flask creer-admin pharmacienne` devient
   `flask creer-admin pharmacienne --nom Elise` (préciser que `--nom` est facultatif). Ajouter
   que la migration `0007` s'applique avec la mise à jour habituelle (`flask db upgrade`).
4. `docs/intent/suivi-presence-pharmacie.md` : ajouter une ligne « IK des admins : voir
   [ik-admin.md](ik-admin.md) ».

---

## 8. Validation finale

```bash
cd backend && .venv/bin/python -m pytest
cd frontend && npm run test:unit && npm run build
cd frontend && npm run test:e2e   # parcours existants : ils doivent rester verts
```
Refaire ensuite la vérification manuelle de la section 6. Faire un commit par section (1 à 7),
avec un message en français (ex. « Ajoute les déplacements IK des admins au tableau du mois »).

## Pièges connus

- `Deplacement.employe_id` devient nullable : **toute** requête sur les déplacements « des
  employés » doit filtrer `employe_id IS NOT NULL` ou passer par un `join(Employe)`. Les endroits
  existants : `services/mois.py` (corrigé en 3.3), `services/absences.py` et `routes/deplacements.py`
  (déjà filtrés par `employe_id` ou par jointure : rien à faire).
- Relations SQLAlchemy vers `utilisateurs` : toujours préciser `foreign_keys=[...]`, sinon
  `AmbiguousForeignKeysError` (à cause de `updated_by_id`).
- Ne pas réutiliser `useSaisieJour` pour les lignes admin : les ids peuvent entrer en collision.
- Arrondis : calculer en `Decimal`, ne convertir en `float` qu'au moment d'écrire dans l'Excel.
- Ne pas ajouter de déplacements admin à `lignes_recap`, `controles` ni `statistiques_annee`.
