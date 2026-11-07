"""Paramètres des indemnités kilométriques (coefficient et nom affiché de l'admin)."""
import pytest

from app.extensions import db
from app.models import Utilisateur


def test_ik_vide_par_defaut(admin):
    reponse = admin.get('/api/parametres/ik')
    assert reponse.status_code == 200
    assert reponse.get_json() == {'coefficient': None, 'nom_affiche': ''}


def test_modification_ik(admin):
    reponse = admin.put('/api/parametres/ik', {'coefficient': '0,636', 'nom_affiche': 'Elise'})
    assert reponse.status_code == 200
    relu = admin.get('/api/parametres/ik').get_json()
    assert relu == {'coefficient': 0.636, 'nom_affiche': 'Elise'}
    assert admin.get('/api/auth/me').get_json()['nom_affiche'] == 'Elise'


@pytest.mark.parametrize('coefficient', [0, -1, 'abc', 10.5, '0,6361', None, 11])
def test_coefficient_invalide_refuse(admin, coefficient):
    reponse = admin.put('/api/parametres/ik', {'coefficient': coefficient, 'nom_affiche': ''})
    assert reponse.status_code == 400


def test_coefficient_refuse_sans_changer_le_nom(admin):
    admin.put('/api/parametres/ik', {'coefficient': '0,5', 'nom_affiche': 'Elise'})
    admin.put('/api/parametres/ik', {'coefficient': '0', 'nom_affiche': 'Autre'})
    assert admin.get('/api/auth/me').get_json()['nom_affiche'] == 'Elise'


def test_libelle_par_defaut_et_nom_vide(app, admin):
    assert admin.put('/api/parametres/ik', {'coefficient': '0,636', 'nom_affiche': '  '}).status_code == 200
    utilisateur = Utilisateur.query.filter_by(identifiant='pharmacienne').one()
    assert utilisateur.nom_affiche is None
    assert utilisateur.libelle == 'pharmacienne'
    db.session.remove()


def test_parametres_ik_reserves_a_l_admin(creer_employe):
    _, session_employe = creer_employe('lea', nom='Martin', prenom='Léa')
    assert session_employe.get('/api/parametres/ik').status_code == 403
    assert session_employe.put('/api/parametres/ik', {'coefficient': '0,636', 'nom_affiche': ''}).status_code == 403
