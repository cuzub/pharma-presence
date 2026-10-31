from datetime import date

from app.extensions import db
from app.models import JourFermeture


def test_employe_ne_saisit_pas_un_dimanche(creer_employe, aujourdhui):
    aujourdhui['date'] = date(2025, 2, 12)
    alice, session = creer_employe('alice')
    reponse = session.put('/api/heures', {'employe_id': alice['id'], 'jour': '2025-02-09', 'minutes': 30})
    assert reponse.status_code == 409
    assert reponse.get_json()['code'] == 'dimanche'


def test_employe_ne_saisit_pas_une_date_future(creer_employe, aujourdhui):
    aujourdhui['date'] = date(2025, 2, 12)
    alice, session = creer_employe('alice')
    reponse = session.put('/api/heures', {'employe_id': alice['id'], 'jour': '2025-02-13', 'minutes': 30})
    assert reponse.status_code == 409
    assert reponse.get_json()['code'] == 'date_future'


def test_employe_ne_saisit_pas_un_jour_de_fermeture(creer_employe, aujourdhui):
    aujourdhui['date'] = date(2025, 2, 12)
    db.session.add(JourFermeture(date=date(2025, 2, 10), libelle='Pont'))
    db.session.commit()
    alice, session = creer_employe('alice')
    reponse = session.put('/api/heures', {'employe_id': alice['id'], 'jour': '2025-02-10', 'minutes': 30})
    assert reponse.status_code == 409
    assert reponse.get_json()['code'] == 'jour_ferme'


def test_deplacement_refuse_sur_jour_bloque(admin, creer_employe, aujourdhui):
    aujourdhui['date'] = date(2025, 2, 12)
    alice, session = creer_employe('alice')
    motif = admin.post('/api/deplacements/motifs', {'libelle': 'Domitis', 'km': 2}).get_json()
    base = {'motif_deplacement_id': motif['id']}
    assert session.post('/api/deplacements', {**base, 'date': '2025-02-09'}).get_json()['code'] == 'dimanche'
    assert session.post('/api/deplacements', {**base, 'date': '2025-02-13'}).get_json()['code'] == 'date_future'


def test_saisie_autorisee_le_jour_meme_et_admin_libre(admin, creer_employe, aujourdhui):
    aujourdhui['date'] = date(2025, 2, 12)
    alice, session = creer_employe('alice')
    assert session.put('/api/heures', {'employe_id': alice['id'], 'jour': '2025-02-12', 'minutes': 30}).status_code == 200
    assert admin.put('/api/heures', {'employe_id': alice['id'], 'jour': '2025-02-09', 'minutes': 30}).status_code == 200


def test_employe_ne_saisit_pas_un_jour_ferie(creer_employe, aujourdhui):
    aujourdhui['date'] = date(2025, 5, 12)
    alice, session = creer_employe('alice')
    reponse = session.put('/api/heures', {'employe_id': alice['id'], 'jour': '2025-05-08', 'minutes': 30})
    assert reponse.status_code == 409
    assert reponse.get_json()['code'] == 'jour_ferie'


def test_feries_calcules_depuis_paques():
    from app.services.feries import est_ferie

    assert est_ferie(date(2025, 4, 21))  # lundi de Pâques 2025
    assert est_ferie(date(2025, 6, 9))  # lundi de Pentecôte 2025
    assert est_ferie(date(2025, 5, 29))  # Ascension 2025
    assert not est_ferie(date(2025, 4, 20))  # dimanche de Pâques (déjà fermé le dimanche)
