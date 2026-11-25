"""Seuils de présents à la fermeture (semaine / samedi)."""
import pytest


def test_seuils_vides_par_defaut(admin):
    assert admin.get('/api/parametres/presence').get_json() == {'seuil_semaine': None, 'seuil_samedi': None}


def test_modification_seuils(admin):
    reponse = admin.put('/api/parametres/presence', {'seuil_semaine': '3', 'seuil_samedi': 2})
    assert reponse.status_code == 200
    assert admin.get('/api/parametres/presence').get_json() == {'seuil_semaine': 3, 'seuil_samedi': 2}
    admin.put('/api/parametres/presence', {'seuil_semaine': '', 'seuil_samedi': None})
    assert admin.get('/api/parametres/presence').get_json() == {'seuil_semaine': None, 'seuil_samedi': None}


@pytest.mark.parametrize('seuil', [-1, 100, '2,5', 'abc', True])
def test_seuil_invalide_refuse(admin, seuil):
    assert admin.put('/api/parametres/presence', {'seuil_semaine': seuil, 'seuil_samedi': 2}).status_code == 400


def test_seuils_reserves_a_l_admin(creer_employe):
    _, session_employe = creer_employe('lea', nom='Martin', prenom='Léa')
    assert session_employe.get('/api/parametres/presence').status_code == 403
    assert session_employe.put('/api/parametres/presence', {'seuil_semaine': 2}).status_code == 403
