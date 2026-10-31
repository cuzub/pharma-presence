from datetime import date

from app.extensions import db
from app.models import HeuresEnPlus


def test_employe_saisit_ses_heures_dans_la_fenetre(creer_employe):
    alice, session = creer_employe('alice')
    reponse = session.put('/api/heures', {'employe_id': alice['id'], 'jour': '2025-02-10', 'minutes': 90})
    assert reponse.status_code == 200
    assert reponse.get_json()['minutes'] == 90
    assert session.get('/api/mois/2025-02').get_json()['employes'][0]['heures'] == {'2025-02-10': 90}


def test_employe_hors_fenetre_refuse_y_compris_effacement(admin, creer_employe, aujourdhui):
    alice, session = creer_employe('alice')
    assert session.put('/api/heures', {'employe_id': alice['id'], 'jour': '2025-02-10', 'minutes': 30}).status_code == 200

    aujourdhui['date'] = date(2025, 3, 6)
    reponse = session.put('/api/heures', {'employe_id': alice['id'], 'jour': '2025-02-10', 'minutes': 45})
    assert reponse.status_code == 403
    assert reponse.get_json()['code'] == 'hors_periode'
    assert session.put('/api/heures', {'employe_id': alice['id'], 'jour': '2025-02-10', 'minutes': 0}).status_code == 403
    # La pharmacienne n'est pas soumise à la fenêtre.
    assert admin.put('/api/heures', {'employe_id': alice['id'], 'jour': '2025-02-10', 'minutes': 45}).status_code == 200


def test_employe_ne_saisit_pas_les_heures_d_un_autre(creer_employe):
    alice, session_alice = creer_employe('alice')
    bruno, _ = creer_employe('bruno', connecter=False)
    assert session_alice.put('/api/heures', {'employe_id': bruno['id'], 'jour': '2025-02-10', 'minutes': 30}).status_code == 404
    assert db.session.query(HeuresEnPlus).filter_by(employe_id=bruno['id']).count() == 0


def test_employe_bloque_pendant_une_absence_bloquante(admin, creer_employe, motifs):
    alice, session = creer_employe('alice')
    absence = admin.post('/api/absences', {
        'employe_id': alice['id'], 'motif_id': motifs['CP'], 'date_debut': '2025-02-03', 'date_reprise': '2025-02-10',
    })
    assert absence.status_code == 201
    reponse = session.put('/api/heures', {'employe_id': alice['id'], 'jour': '2025-02-05', 'minutes': 30})
    assert reponse.status_code == 409
    assert reponse.get_json()['code'] == 'jour_absent'


def test_saisie_refusee_avant_le_contrat(admin, creer_employe):
    alice, session = creer_employe('alice', date_entree='2025-02-10')
    reponse = session.put('/api/heures', {'employe_id': alice['id'], 'jour': '2025-02-05', 'minutes': 30})
    assert reponse.status_code == 409
    assert reponse.get_json()['code'] == 'hors_contrat'
    assert admin.put('/api/heures', {'employe_id': alice['id'], 'jour': '2025-02-05', 'minutes': 30}).status_code == 409
    assert session.put('/api/heures', {'employe_id': alice['id'], 'jour': '2025-02-10', 'minutes': 30}).status_code == 200
