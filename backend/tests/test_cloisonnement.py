"""Un employé ne doit jamais voir ni modifier les données d'un autre employé."""

import pytest


@pytest.fixture
def deux_employes(admin, creer_employe, motifs):
    alice, session_alice = creer_employe('alice', nom='ALPHA')
    bruno, session_bruno = creer_employe('bruno', nom='BRAVO')
    for fiche in (alice, bruno):
        assert admin.post('/api/absences', {
            'employe_id': fiche['id'], 'motif_id': motifs['MAL'], 'date_debut': '2025-01-06', 'date_reprise': '2025-01-08',
        }).status_code == 201
        assert admin.put('/api/heures', {'employe_id': fiche['id'], 'jour': '2025-01-10', 'heures': 2}).status_code == 200
    return alice, session_alice, bruno, session_bruno


def test_employe_ne_voit_que_ses_absences(deux_employes):
    alice, session_alice, _, _ = deux_employes
    absences = session_alice.get('/api/absences?employe_id=999').get_json()
    assert len(absences) == 1
    assert {a['employe_id'] for a in absences} == {alice['id']}


def test_employe_ne_voit_que_son_mois(deux_employes):
    alice, session_alice, _, _ = deux_employes
    mois = session_alice.get('/api/mois/2025-01').get_json()
    assert [e['id'] for e in mois['employes']] == [alice['id']]


def test_employe_n_accede_pas_aux_routes_admin(deux_employes, motifs):
    alice, session_alice, bruno, _ = deux_employes
    assert session_alice.get('/api/employes').status_code == 403
    assert session_alice.get(f"/api/employes/{bruno['id']}").status_code == 403
    assert session_alice.put('/api/heures', {'employe_id': alice['id'], 'jour': '2025-01-11', 'heures': 1}).status_code == 403
    assert session_alice.post('/api/absences', {
        'employe_id': alice['id'], 'motif_id': motifs['CP'], 'date_debut': '2025-02-01',
    }).status_code == 403
    assert session_alice.get('/api/exports/2025-01/controles').status_code == 403
    assert session_alice.get('/api/exports/2025-01/etat-preparatoire.xlsx').status_code == 403
    assert session_alice.post('/api/motifs', {'code': 'X', 'libelle': 'X'}).status_code == 403


def test_deplacements_cloisonnes(deux_employes):
    alice, session_alice, bruno, session_bruno = deux_employes
    trajet = {'date': '2025-01-15', 'depart': 'Pharmacie', 'arrivee': 'Grossiste', 'motif': 'Commande', 'km': 12}

    # employe_id fourni par le client : ignoré, le déplacement est rattaché à l'employé connecté.
    cree = session_alice.post('/api/deplacements', {**trajet, 'employe_id': bruno['id']})
    assert cree.status_code == 201
    assert cree.get_json()['employe_id'] == alice['id']
    assert cree.get_json()['statut'] == 'en_attente'
    deplacement_id = cree.get_json()['id']

    assert session_bruno.get('/api/deplacements').get_json() == []
    assert session_bruno.put(f'/api/deplacements/{deplacement_id}', trajet).status_code == 404
    assert session_bruno.delete(f'/api/deplacements/{deplacement_id}').status_code == 404
    assert session_bruno.post(f'/api/deplacements/{deplacement_id}/valider').status_code == 403


def test_deplacement_valide_non_modifiable_par_employe(admin, deux_employes):
    _, session_alice, _, _ = deux_employes
    trajet = {'date': '2025-01-15', 'depart': 'Pharmacie', 'arrivee': 'Grossiste', 'motif': 'Commande', 'km': 12}
    deplacement_id = session_alice.post('/api/deplacements', trajet).get_json()['id']

    modifie = session_alice.put(f'/api/deplacements/{deplacement_id}', {**trajet, 'km': 15})
    assert modifie.status_code == 200
    assert modifie.get_json()['km'] == 15

    assert admin.post(f'/api/deplacements/{deplacement_id}/valider').get_json()['statut'] == 'valide'
    assert session_alice.put(f'/api/deplacements/{deplacement_id}', trajet).status_code == 409
    assert session_alice.delete(f'/api/deplacements/{deplacement_id}').status_code == 409


def test_deplacement_refuse_puis_corrige_repasse_en_attente(admin, deux_employes):
    _, session_alice, _, _ = deux_employes
    trajet = {'date': '2025-01-15', 'depart': 'Pharmacie', 'arrivee': 'Grossiste', 'motif': 'Commande', 'km': 120}
    deplacement_id = session_alice.post('/api/deplacements', trajet).get_json()['id']

    refuse = admin.post(f'/api/deplacements/{deplacement_id}/refuser', {'motif_refus': 'Distance erronée'})
    assert refuse.get_json()['statut'] == 'refuse'

    corrige = session_alice.put(f'/api/deplacements/{deplacement_id}', {**trajet, 'km': 12})
    assert corrige.get_json()['statut'] == 'en_attente'
    assert corrige.get_json()['motif_refus'] is None
