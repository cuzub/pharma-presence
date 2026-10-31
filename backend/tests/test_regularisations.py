"""Régularisations d'heures +/- (crédits / débits) et solde cumulé."""

from app.extensions import db
from app.models import JournalModification, RegularisationHeures


def _regulariser(admin, employe_id, jour, minutes, commentaire=None):
    reponse = admin.post(f'/api/employes/{employe_id}/regularisations', {
        'jour': jour, 'minutes': minutes, 'commentaire': commentaire,
    })
    assert reponse.status_code == 201, reponse.get_json()
    return reponse.get_json()


def _ligne(session, mois, employe_id):
    donnees = session.get(f'/api/mois/{mois}').get_json()
    return next(e for e in donnees['employes'] if e['id'] == employe_id)


def test_creer_modifier_supprimer_et_journal(admin, creer_employe):
    alice, _ = creer_employe('alice', connecter=False)
    regularisation = _regulariser(admin, alice['id'], '2025-02-03', -1200, 'Heures payées en janvier')
    assert regularisation['minutes'] == -1200
    assert regularisation['commentaire'] == 'Heures payées en janvier'

    liste = admin.get(f"/api/employes/{alice['id']}/regularisations").get_json()
    assert liste['solde_minutes'] == -1200
    assert [r['id'] for r in liste['regularisations']] == [regularisation['id']]

    modifiee = admin.put(f"/api/regularisations/{regularisation['id']}", {'jour': '2025-02-03', 'minutes': -600, 'commentaire': ''})
    assert modifiee.status_code == 200
    assert modifiee.get_json()['commentaire'] is None

    assert admin.delete(f"/api/regularisations/{regularisation['id']}").status_code == 204
    assert db.session.query(RegularisationHeures).count() == 0

    actions = [j.action for j in JournalModification.query.filter_by(type='regularisation').order_by(JournalModification.id)]
    assert actions == ['creation', 'modification', 'suppression']
    filtre = admin.get('/api/journal', query_string={'type': 'regularisation'}).get_json()
    assert filtre['total'] == 3


def test_validation(admin, creer_employe):
    alice, _ = creer_employe('alice', connecter=False)
    url = f"/api/employes/{alice['id']}/regularisations"
    for minutes in (0, 7, 30005, 'abc', None, True):
        assert admin.post(url, {'jour': '2025-02-03', 'minutes': minutes}).status_code == 400, minutes
    assert admin.post(url, {'jour': 'hier', 'minutes': 60}).status_code == 400
    assert admin.post(url, {'jour': '2025-02-03', 'minutes': 60, 'commentaire': 'x' * 201}).status_code == 400
    assert admin.post('/api/employes/999999/regularisations', {'jour': '2025-02-03', 'minutes': 60}).status_code == 404
    assert admin.put('/api/regularisations/999999', {'jour': '2025-02-03', 'minutes': 60}).status_code == 404


def test_reservee_a_la_pharmacienne(admin, creer_employe):
    alice, session = creer_employe('alice')
    regularisation = _regulariser(admin, alice['id'], '2025-02-03', 60)
    assert session.get(f"/api/employes/{alice['id']}/regularisations").status_code == 403
    assert session.post(f"/api/employes/{alice['id']}/regularisations", {'jour': '2025-02-03', 'minutes': 60}).status_code == 403
    assert session.put(f"/api/regularisations/{regularisation['id']}", {'jour': '2025-02-03', 'minutes': 5}).status_code == 403
    assert session.delete(f"/api/regularisations/{regularisation['id']}").status_code == 403


def test_pas_soumise_aux_absences_bloquantes(admin, creer_employe, motifs):
    alice, _ = creer_employe('alice', connecter=False)
    admin.post('/api/absences', {
        'employe_id': alice['id'], 'motif_id': motifs['RECUP'], 'date_debut': '2025-02-03', 'date_reprise': '2025-02-04',
    })
    _regulariser(admin, alice['id'], '2025-02-03', -420, 'Récup du 03/02')


def test_solde_cumule_a_fin_de_mois_et_net_du_mois(admin, creer_employe):
    alice, session = creer_employe('alice')
    admin.put('/api/heures', {'employe_id': alice['id'], 'jour': '2024-12-10', 'minutes': 120})
    _regulariser(admin, alice['id'], '2024-12-31', 600, 'Solde de départ')
    admin.put('/api/heures', {'employe_id': alice['id'], 'jour': '2025-01-15', 'minutes': 90})
    _regulariser(admin, alice['id'], '2025-01-31', -300, 'Heures payées')
    admin.put('/api/heures', {'employe_id': alice['id'], 'jour': '2025-02-10', 'minutes': -30})

    decembre = _ligne(admin, '2024-12', alice['id'])
    assert (decembre['total_minutes'], decembre['solde_minutes']) == (720, 720)

    janvier = _ligne(admin, '2025-01', alice['id'])
    assert (janvier['total_minutes'], janvier['solde_minutes']) == (-210, 510)
    assert [(r['jour'], r['minutes'], r['commentaire']) for r in janvier['regularisations']] == [
        ('2025-01-31', -300, 'Heures payées'),
    ]

    fevrier = _ligne(admin, '2025-02', alice['id'])
    assert (fevrier['total_minutes'], fevrier['solde_minutes']) == (-30, 480)

    # L'employé voit ses régularisations et son solde (lecture seule).
    vue_employe = session.get('/api/mois/2025-01').get_json()['employes'][0]
    assert vue_employe['solde_minutes'] == 510
    assert len(vue_employe['regularisations']) == 1

    # Le solde « à ce jour » (3 février 2025) de la fiche employé : le -30 du 10 février n'est pas encore compté.
    assert admin.get(f"/api/employes/{alice['id']}/regularisations").get_json()['solde_minutes'] == 510


def test_incluses_dans_les_statistiques(admin, creer_employe):
    alice, _ = creer_employe('alice', nom='ALICE', connecter=False)
    admin.put('/api/heures', {'employe_id': alice['id'], 'jour': '2025-03-10', 'minutes': 90})
    _regulariser(admin, alice['id'], '2025-03-31', -600)
    _regulariser(admin, alice['id'], '2025-04-01', 120)

    stats = next(e for e in admin.get('/api/statistiques/2025').get_json()['employes'] if e['nom'] == 'ALICE')
    assert stats['plus'][2:4] == [90, 120]
    assert stats['moins'][2:4] == [-600, 0]
    assert stats['total_net'] == -390


def test_regularisation_seule_absente_de_l_export(admin, creer_employe):
    parti, _ = creer_employe('lucie', nom='Parti', date_entree='2024-01-01', connecter=False)
    admin.post(f"/api/employes/{parti['id']}/depart", {'date_sortie': '2025-01-31'})
    _regulariser(admin, parti['id'], '2025-02-05', -300, 'Solde payé au départ')

    # Visible dans le tableau du mois...
    assert any(e['id'] == parti['id'] for e in admin.get('/api/mois/2025-02').get_json()['employes'])
    # ... mais pas dans l'export pour le comptable.
    csv = admin.get('/api/exports/2025-02/recap.csv').get_data(as_text=True)
    assert 'PARTI' not in csv.upper()
    controles = admin.get('/api/exports/2025-02/controles').get_json()
    assert not any('Parti' in message for message in controles['avertissements'])
