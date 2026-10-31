from datetime import date

import pytest
from flask_migrate import downgrade, upgrade
from sqlalchemy import text

from app import create_app
from app.extensions import db
from app.models import Utilisateur

ADMIN_MDP = 'admin-mot-de-passe-test'
EMPLOYE_MDP_PROVISOIRE = 'provisoire-12345'
EMPLOYE_MDP = 'employe-mot-de-passe-test'

_TABLES = ['journal_modifications', 'heures_en_plus', 'regularisations_heures', 'deplacements', 'motifs_deplacement', 'absences', 'contrats', 'employes', 'jours_fermeture']


@pytest.fixture(scope='session')
def app():
    app = create_app('testing')
    with app.app_context():
        downgrade(revision='base')
        upgrade()
        yield app
        db.session.remove()


@pytest.fixture(autouse=True)
def aujourdhui(monkeypatch):
    """Date du jour figée (3 février 2025 : janvier et février sont modifiables par l'employé)."""
    from app.services import fenetre

    reference = {'date': date(2025, 2, 3)}
    monkeypatch.setattr(fenetre, 'aujourdhui', lambda: reference['date'])
    return reference


@pytest.fixture(autouse=True)
def base_propre(app):
    yield
    db.session.rollback()
    for table in _TABLES:
        db.session.execute(text(f'DELETE FROM {table}'))
    db.session.execute(text("DELETE FROM motifs_absence WHERE code NOT IN ('CP','MAL','RECUP','MAT','PAT','SS','FORM','AUTRE')"))
    db.session.execute(text('UPDATE motifs_absence SET updated_by_id = NULL'))
    db.session.execute(text("UPDATE motifs_absence SET bloque_saisie = (code NOT IN ('FORM', 'AUTRE'))"))
    db.session.execute(text('DELETE FROM utilisateurs'))
    db.session.commit()
    db.session.remove()


class Session:
    """Client HTTP d'un utilisateur connecté (cookie de session + jeton CSRF)."""

    def __init__(self, app):
        self.client = app.test_client()

    def login(self, identifiant, mot_de_passe):
        return self.client.post('/api/auth/login', json={'identifiant': identifiant, 'mot_de_passe': mot_de_passe})

    def _csrf(self):
        cookie = self.client.get_cookie('pharma_csrf_access_token')
        return {'X-CSRF-TOKEN': cookie.value} if cookie else {}

    def get(self, url, **kwargs):
        return self.client.get(url, **kwargs)

    def post(self, url, json=None):
        return self.client.post(url, json=json if json is not None else {}, headers=self._csrf())

    def put(self, url, json=None):
        return self.client.put(url, json=json if json is not None else {}, headers=self._csrf())

    def delete(self, url):
        return self.client.delete(url, headers=self._csrf())


@pytest.fixture
def admin(app):
    utilisateur = Utilisateur(identifiant='pharmacienne', role=Utilisateur.ROLE_ADMIN)
    utilisateur.definir_mot_de_passe(ADMIN_MDP, provisoire=False)
    db.session.add(utilisateur)
    db.session.commit()
    session = Session(app)
    assert session.login('pharmacienne', ADMIN_MDP).status_code == 200
    return session


@pytest.fixture
def creer_employe(app, admin):
    """Crée un employé via l'API et renvoie (fiche, session connectée avec mot de passe définitif)."""

    def _creer(identifiant, nom='TEST', prenom=None, date_entree='2025-01-01', heures=151.67, connecter=True):
        reponse = admin.post('/api/employes', {
            'nom': nom,
            'prenom': prenom or identifiant.capitalize(),
            'identifiant': identifiant,
            'date_entree': date_entree,
            'heures_mensuelles': heures,
            'mot_de_passe_provisoire': EMPLOYE_MDP_PROVISOIRE,
        })
        assert reponse.status_code == 201, reponse.get_json()
        fiche = reponse.get_json()
        if not connecter:
            return fiche, None
        session = Session(app)
        assert session.login(identifiant, EMPLOYE_MDP_PROVISOIRE).status_code == 200
        changement = session.post('/api/auth/mot-de-passe', {
            'mot_de_passe_actuel': EMPLOYE_MDP_PROVISOIRE, 'nouveau_mot_de_passe': EMPLOYE_MDP,
        })
        assert changement.status_code == 200, changement.get_json()
        return fiche, session

    return _creer


@pytest.fixture
def motifs(admin):
    return {m['code']: m['id'] for m in admin.get('/api/motifs').get_json()}
