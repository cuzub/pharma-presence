"""Blocage de la saisie pendant les absences : heures, déplacements, conflits d'absence et journal."""

from datetime import date

import pytest

from app.extensions import db
from app.models import Deplacement, HeuresEnPlus, JournalModification


@pytest.fixture
def alice(creer_employe):
    fiche, session = creer_employe('alice', connecter=True)
    return fiche, session


def _absence(admin, employe_id, motif_id, debut, reprise=None, **extra):
    return admin.post('/api/absences', {
        'employe_id': employe_id, 'motif_id': motif_id, 'date_debut': debut, 'date_reprise': reprise, **extra,
    })


def _heures(admin, employe_id, jour, minutes):
    return admin.put('/api/heures', {'employe_id': employe_id, 'jour': jour, 'minutes': minutes})


def _deplacement_autre(session_ou_admin, date, employe_id=None):
    corps = {'date': date, 'motif': 'Visite', 'km': 4}
    if employe_id is not None:
        corps['employe_id'] = employe_id
    return session_ou_admin.post('/api/deplacements', corps)


def test_motifs_formation_et_autre_ne_bloquent_pas(admin, motifs):
    par_code = {m['code']: m for m in admin.get('/api/motifs').get_json()}
    assert par_code['CP']['bloque_saisie'] is True
    assert par_code['MAL']['bloque_saisie'] is True
    assert par_code['FORM']['bloque_saisie'] is False
    assert par_code['AUTRE']['bloque_saisie'] is False


def test_heures_refusees_pendant_une_absence_bloquante(admin, alice, motifs):
    fiche, _ = alice
    assert _absence(admin, fiche['id'], motifs['CP'], '2025-01-10', '2025-01-15').status_code == 201

    reponse = _heures(admin, fiche['id'], '2025-01-12', 90)
    assert reponse.status_code == 409
    assert reponse.get_json()['code'] == 'jour_absent'
    assert reponse.get_json()['message'] == 'Alice est absente le 12/01/2025 (Congés payés) : saisie impossible'
    assert _heures(admin, fiche['id'], '2025-01-15', 90).status_code == 200


def test_effacement_des_heures_toujours_permis(admin, alice, motifs):
    fiche, _ = alice
    _absence(admin, fiche['id'], motifs['CP'], '2025-01-10', '2025-01-15')
    # Saisie antérieure à l'absence (insérée directement) : seul l'effacement reste possible.
    db.session.add(HeuresEnPlus(employe_id=fiche['id'], jour=date(2025, 1, 12), minutes=45))
    db.session.commit()
    assert _heures(admin, fiche['id'], '2025-01-12', 0).status_code == 200
    assert HeuresEnPlus.query.filter_by(employe_id=fiche['id']).count() == 0


def test_formation_autorisee_pendant_la_formation(admin, alice, motifs):
    fiche, _ = alice
    assert _absence(admin, fiche['id'], motifs['FORM'], '2025-01-10', '2025-01-15').status_code == 201
    assert _heures(admin, fiche['id'], '2025-01-12', 60).status_code == 200


def test_deplacements_refuses_pour_admin_et_employe(admin, alice, motifs):
    fiche, session = alice
    _absence(admin, fiche['id'], motifs['CP'], '2025-01-10', '2025-01-15')

    par_employe = session.post('/api/deplacements', {'date': '2025-01-12', 'motif': 'Visite', 'km': 4})
    assert par_employe.status_code == 409
    assert par_employe.get_json()['code'] == 'jour_absent'
    assert _deplacement_autre(admin, '2025-01-12', fiche['id']).status_code == 409
    assert _deplacement_autre(session, '2025-01-16').status_code == 201


def test_modifier_un_deplacement_vers_un_jour_absent_refuse(admin, alice, motifs):
    fiche, session = alice
    cree = _deplacement_autre(session, '2025-01-16').get_json()
    _absence(admin, fiche['id'], motifs['CP'], '2025-01-10', '2025-01-15')

    reponse = session.put(f"/api/deplacements/{cree['id']}", {'date': '2025-01-12', 'motif': 'Visite', 'km': 4})
    assert reponse.status_code == 409
    assert reponse.get_json()['code'] == 'jour_absent'


def test_suppression_de_deplacement_toujours_permise(admin, alice, motifs):
    fiche, session = alice
    # Déplacement saisi pendant une formation (non bloquante), puis la formation devient bloquante.
    _absence(admin, fiche['id'], motifs['FORM'], '2025-01-10', '2025-01-15')
    cree = _deplacement_autre(session, '2025-01-12').get_json()
    admin.put(f"/api/motifs/{motifs['FORM']}", {'libelle': 'Formation', 'couleur': '#0dcaf0', 'bloque_saisie': True})

    assert _deplacement_autre(session, '2025-01-11').status_code == 409
    assert session.delete(f"/api/deplacements/{cree['id']}").status_code == 204


def test_absence_en_conflit_renvoie_la_liste_puis_confirmee(admin, alice, motifs):
    fiche, session = alice
    _heures(admin, fiche['id'], '2025-01-13', 90)
    _deplacement_autre(admin, '2025-01-14', fiche['id'])

    reponse = _absence(admin, fiche['id'], motifs['CP'], '2025-01-10', '2025-01-20')
    assert reponse.status_code == 409
    corps = reponse.get_json()
    assert corps['code'] == 'saisies_en_conflit'
    assert [(c['type'], c['jour'], c['libelle']) for c in corps['conflits']] == [
        ('heures', '2025-01-13', '+1h30'),
        ('deplacement', '2025-01-14', 'Visite 4 km'),
    ]
    assert Deplacement.query.filter_by(employe_id=fiche['id']).count() == 1
    assert HeuresEnPlus.query.filter_by(employe_id=fiche['id']).count() == 1

    confirmee = _absence(admin, fiche['id'], motifs['CP'], '2025-01-10', '2025-01-20', confirmer_suppression=True)
    assert confirmee.status_code == 201
    assert HeuresEnPlus.query.filter_by(employe_id=fiche['id']).count() == 0
    assert Deplacement.query.filter_by(employe_id=fiche['id']).count() == 0

    suppressions = JournalModification.query.filter_by(employe_id=fiche['id'], action='suppression').all()
    assert sorted(s.type for s in suppressions) == ['deplacement', 'heures']
    assert all(s.auteur_identifiant == 'pharmacienne' for s in suppressions)


def test_absence_en_cours_couvre_les_dates_suivantes(admin, alice, motifs):
    fiche, _ = alice
    _absence(admin, fiche['id'], motifs['MAT'], '2025-02-01')
    assert _heures(admin, fiche['id'], '2025-06-01', 30).status_code == 409


def test_absence_en_cours_en_conflit_avec_saisies_futures(admin, alice, motifs):
    fiche, _ = alice
    _heures(admin, fiche['id'], '2025-06-01', 30)
    reponse = _absence(admin, fiche['id'], motifs['MAT'], '2025-02-01')
    assert reponse.status_code == 409
    assert reponse.get_json()['conflits'][0]['jour'] == '2025-06-01'


def test_modification_qui_etend_l_absence_demande_confirmation(admin, alice, motifs):
    fiche, _ = alice
    absence_id = _absence(admin, fiche['id'], motifs['CP'], '2025-01-10', '2025-01-12').get_json()['id']
    _heures(admin, fiche['id'], '2025-01-14', -30)

    etendue = {'employe_id': fiche['id'], 'motif_id': motifs['CP'], 'date_debut': '2025-01-10', 'date_reprise': '2025-01-16'}
    reponse = admin.put(f'/api/absences/{absence_id}', etendue)
    assert reponse.status_code == 409
    assert reponse.get_json()['conflits'][0]['libelle'] == '-30min'

    confirmee = admin.put(f'/api/absences/{absence_id}', {**etendue, 'confirmer_suppression': True})
    assert confirmee.status_code == 200
    assert HeuresEnPlus.query.filter_by(employe_id=fiche['id']).count() == 0
    assert JournalModification.query.filter_by(employe_id=fiche['id'], type='heures', action='suppression').count() == 1


def test_absence_non_bloquante_ne_cree_pas_de_conflit(admin, alice, motifs):
    fiche, _ = alice
    _heures(admin, fiche['id'], '2025-01-13', 60)
    assert _absence(admin, fiche['id'], motifs['FORM'], '2025-01-10', '2025-01-20').status_code == 201
    assert HeuresEnPlus.query.filter_by(employe_id=fiche['id']).count() == 1


