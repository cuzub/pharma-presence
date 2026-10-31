"""Statistiques annuelles des heures en plus / en moins."""


def _stats(session, annee=2025):
    return session.get(f'/api/statistiques/{annee}')


def _par_nom(donnees):
    return {e['nom']: e for e in donnees['employes']}


def test_plus_moins_net_par_mois_et_totaux(admin, creer_employe):
    alice, _ = creer_employe('alice', nom='ALICE', connecter=False)
    bruno, _ = creer_employe('bruno', nom='BRUNO', connecter=False)
    admin.put('/api/heures', {'employe_id': alice['id'], 'jour': '2025-01-10', 'minutes': 90})
    admin.put('/api/heures', {'employe_id': alice['id'], 'jour': '2025-01-11', 'minutes': -30})
    admin.put('/api/heures', {'employe_id': alice['id'], 'jour': '2025-03-10', 'minutes': 60})
    admin.put('/api/heures', {'employe_id': bruno['id'], 'jour': '2025-02-03', 'minutes': -60})

    reponse = _stats(admin)
    assert reponse.status_code == 200
    donnees = reponse.get_json()
    assert donnees['annee'] == 2025
    alice_stats = _par_nom(donnees)['ALICE']
    assert alice_stats['plus'] == [90, 0, 60] + [0] * 9
    assert alice_stats['moins'] == [-30, 0, 0] + [0] * 9
    assert alice_stats['net'] == [60, 0, 60] + [0] * 9
    assert (alice_stats['total_plus'], alice_stats['total_moins'], alice_stats['total_net']) == (150, -30, 120)

    totaux = donnees['totaux']
    assert totaux['plus'] == [90, 0, 60] + [0] * 9
    assert totaux['moins'] == [-30, -60, 0] + [0] * 9
    assert totaux['net'] == [60, -60, 60] + [0] * 9
    assert (totaux['total_plus'], totaux['total_moins'], totaux['total_net']) == (150, -90, 60)


def test_entrees_des_autres_annees_ignorees(admin, creer_employe):
    alice, _ = creer_employe('alice', nom='ALICE', connecter=False)
    admin.put('/api/heures', {'employe_id': alice['id'], 'jour': '2024-12-31', 'minutes': 120})
    admin.put('/api/heures', {'employe_id': alice['id'], 'jour': '2026-01-01', 'minutes': -120})
    admin.put('/api/heures', {'employe_id': alice['id'], 'jour': '2025-12-31', 'minutes': 15})

    donnees = _stats(admin).get_json()
    alice_stats = _par_nom(donnees)['ALICE']
    assert alice_stats['plus'][11] == 15 and alice_stats['total_plus'] == 15
    assert alice_stats['total_moins'] == 0
    assert donnees['totaux']['total_net'] == 15


def test_employe_sous_contrat_sans_heures_inclus_a_zero(admin, creer_employe):
    creer_employe('carla', nom='CARLA', connecter=False)

    donnees = _stats(admin).get_json()
    carla = _par_nom(donnees)['CARLA']
    assert carla['actif'] is True
    assert carla['net'] == [0] * 12 and carla['total_net'] == 0
    assert donnees['totaux']['total_net'] == 0


def test_employe_parti_inclus_avec_actif_faux(admin, creer_employe):
    dave, _ = creer_employe('dave', nom='DAVE', connecter=False)
    admin.put('/api/heures', {'employe_id': dave['id'], 'jour': '2025-02-10', 'minutes': 30})
    assert admin.post(f"/api/employes/{dave['id']}/depart", {'date_sortie': '2025-06-30'}).status_code == 200

    dave_stats = _par_nom(_stats(admin).get_json())['DAVE']
    assert dave_stats['actif'] is False
    assert dave_stats['total_plus'] == 30


def test_employe_hors_annee_et_sans_heures_exclu(admin, creer_employe):
    eve, _ = creer_employe('eve', nom='EVE', date_entree='2024-01-01', connecter=False)
    assert admin.post(f"/api/employes/{eve['id']}/depart", {'date_sortie': '2024-06-30'}).status_code == 200
    creer_employe('fanny', nom='FANNY', date_entree='2026-03-01', connecter=False)
    creer_employe('gaspard', nom='GASPARD', connecter=False)

    noms = [e['nom'] for e in _stats(admin).get_json()['employes']]
    assert 'EVE' not in noms and 'FANNY' not in noms
    assert 'GASPARD' in noms


def test_employes_tries_par_nom_et_prenom(admin, creer_employe):
    creer_employe('zoe', nom='ZOE', prenom='Zoe', connecter=False)
    creer_employe('ana', nom='ABEL', prenom='Ana', connecter=False)
    creer_employe('ben', nom='ABEL', prenom='Ben', connecter=False)

    donnees = _stats(admin).get_json()
    assert [(e['nom'], e['prenom']) for e in donnees['employes']] == [('ABEL', 'Ana'), ('ABEL', 'Ben'), ('ZOE', 'Zoe')]


def test_annee_sans_donnees(admin):
    donnees = _stats(admin, 2030).get_json()
    assert donnees['employes'] == []
    assert donnees['totaux']['total_net'] == 0 and donnees['totaux']['net'] == [0] * 12


def test_acces_reserve_aux_admins(creer_employe):
    _, session_alice = creer_employe('alice')
    assert _stats(session_alice).status_code == 403


def test_annee_invalide(admin):
    assert _stats(admin, 1999).status_code == 400
    assert _stats(admin, 2101).status_code == 400
