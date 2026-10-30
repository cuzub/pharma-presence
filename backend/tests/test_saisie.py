import pytest
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import Absence


@pytest.fixture
def alice(creer_employe):
    fiche, _ = creer_employe('alice', connecter=False)
    return fiche


def _absence(admin, employe_id, motif_id, debut, reprise=None):
    return admin.post('/api/absences', {
        'employe_id': employe_id, 'motif_id': motif_id, 'date_debut': debut, 'date_reprise': reprise,
    })


def test_absence_par_periode(admin, alice, motifs):
    reponse = _absence(admin, alice['id'], motifs['CP'], '2025-01-20', '2025-01-27')
    assert reponse.status_code == 201
    absence = reponse.get_json()
    assert absence['motif_libelle'] == 'Congés payés'
    assert absence['date_reprise'] == '2025-01-27'


def test_reprise_doit_suivre_le_debut(admin, alice, motifs):
    assert _absence(admin, alice['id'], motifs['CP'], '2025-01-20', '2025-01-20').status_code == 400


def test_chevauchement_refuse_avec_message_clair(admin, alice, motifs):
    _absence(admin, alice['id'], motifs['CP'], '2025-01-20', '2025-01-27')
    reponse = _absence(admin, alice['id'], motifs['MAL'], '2025-01-26', '2025-01-29')
    assert reponse.status_code == 409
    assert 'Congés payés' in reponse.get_json()['message']


def test_absences_contigues_acceptees(admin, alice, motifs):
    _absence(admin, alice['id'], motifs['CP'], '2025-01-20', '2025-01-27')
    assert _absence(admin, alice['id'], motifs['MAL'], '2025-01-27', '2025-01-29').status_code == 201


def test_absence_en_cours_bloque_les_suivantes(admin, alice, motifs):
    _absence(admin, alice['id'], motifs['MAT'], '2025-02-01')
    assert _absence(admin, alice['id'], motifs['CP'], '2025-06-01', '2025-06-08').status_code == 409


def test_contrainte_base_de_donnees_anti_chevauchement(app, admin, alice, motifs):
    """Même en contournant l'API, PostgreSQL refuse deux absences qui se chevauchent."""
    db.session.add(Absence(employe_id=alice['id'], motif_id=motifs['CP'], date_debut=_d('2025-03-03'), date_reprise=_d('2025-03-10')))
    db.session.commit()
    db.session.add(Absence(employe_id=alice['id'], motif_id=motifs['MAL'], date_debut=_d('2025-03-05'), date_reprise=_d('2025-03-06')))
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_modifier_absence_sans_se_chevaucher_elle_meme(admin, alice, motifs):
    absence_id = _absence(admin, alice['id'], motifs['CP'], '2025-01-20', '2025-01-27').get_json()['id']
    reponse = admin.put(f'/api/absences/{absence_id}', {
        'employe_id': alice['id'], 'motif_id': motifs['CP'], 'date_debut': '2025-01-21', 'date_reprise': '2025-01-28',
    })
    assert reponse.status_code == 200
    assert admin.delete(f'/api/absences/{absence_id}').status_code == 204


def test_heures_en_plus_upsert_et_suppression(admin, alice):
    url = '/api/heures'
    assert admin.put(url, {'employe_id': alice['id'], 'jour': '2025-01-10', 'heures': '1,5'}).get_json()['heures'] == 1.5
    assert admin.put(url, {'employe_id': alice['id'], 'jour': '2025-01-10', 'heures': 2.25}).get_json()['heures'] == 2.25
    mois = admin.get('/api/mois/2025-01').get_json()
    assert mois['employes'][0]['heures'] == {'2025-01-10': 2.25}

    assert admin.put(url, {'employe_id': alice['id'], 'jour': '2025-01-10', 'heures': 0}).status_code == 200
    assert admin.get('/api/mois/2025-01').get_json()['employes'][0]['heures'] == {}


@pytest.mark.parametrize('valeur', [1.1, -1, 25, 'abc'])
def test_heures_en_plus_invalides(admin, alice, valeur):
    assert admin.put('/api/heures', {'employe_id': alice['id'], 'jour': '2025-01-10', 'heures': valeur}).status_code == 400


def test_motifs_et_jours_fermeture(admin):
    motif = admin.post('/api/motifs', {'code': 'evt', 'libelle': 'Événement familial', 'couleur': '#123456'})
    assert motif.status_code == 201
    assert motif.get_json()['code'] == 'EVT'
    assert admin.put(f"/api/motifs/{motif.get_json()['id']}", {'libelle': 'Évt familial', 'couleur': '#123456', 'actif': False}).get_json()['actif'] is False

    fermeture = admin.post('/api/jours-fermeture', {'date': '2025-08-16', 'libelle': 'Pont'})
    assert fermeture.status_code == 201
    assert admin.post('/api/jours-fermeture', {'date': '2025-08-16'}).status_code == 409
    assert admin.get('/api/mois/2025-08').get_json()['jours_fermeture'][0]['date'] == '2025-08-16'


def _d(valeur):
    from datetime import date
    return date.fromisoformat(valeur)
