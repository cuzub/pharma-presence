from tests.conftest import EMPLOYE_MDP_PROVISOIRE, Session


def test_creer_employe(admin, creer_employe):
    fiche, _ = creer_employe('alice', nom='Martin', date_entree='2025-02-10', heures=121.33, connecter=False)
    assert fiche['identifiant'] == 'alice'
    assert fiche['date_entree'] == '2025-02-10'
    assert fiche['date_sortie'] is None
    assert fiche['heures_mensuelles'] == 121.33
    assert fiche['actif'] is True
    assert [e['id'] for e in admin.get('/api/employes').get_json()] == [fiche['id']]


def test_identifiant_unique_et_valide(admin, creer_employe):
    creer_employe('alice', connecter=False)
    base = {'nom': 'X', 'prenom': 'Y', 'date_entree': '2025-01-01', 'heures_mensuelles': 100,
            'mot_de_passe_provisoire': EMPLOYE_MDP_PROVISOIRE}
    assert admin.post('/api/employes', {**base, 'identifiant': 'Alice'}).status_code == 409
    assert admin.post('/api/employes', {**base, 'identifiant': 'a b'}).status_code == 400
    assert admin.post('/api/employes', {**base, 'identifiant': 'bob', 'mot_de_passe_provisoire': 'court'}).status_code == 400


def test_avenant_cloture_le_contrat_precedent(admin, creer_employe):
    fiche, _ = creer_employe('alice', date_entree='2025-01-01', heures=151.67, connecter=False)
    reponse = admin.post(f"/api/employes/{fiche['id']}/contrats", {'heures_mensuelles': 121.33, 'date_debut': '2025-03-15'})
    assert reponse.status_code == 201
    contrats = reponse.get_json()['contrats']
    assert [(c['date_debut'], c['date_fin'], c['heures_mensuelles']) for c in contrats] == [
        ('2025-01-01', '2025-03-14', 151.67),
        ('2025-03-15', None, 121.33),
    ]
    # Un avenant n'interrompt pas la période d'emploi.
    assert reponse.get_json()['date_entree'] == '2025-01-01'


def test_correction_de_contrat_qui_chevauche_refusee(admin, creer_employe):
    fiche, _ = creer_employe('alice', date_entree='2025-01-01', connecter=False)
    contrats = admin.post(f"/api/employes/{fiche['id']}/contrats", {'heures_mensuelles': 100, 'date_debut': '2025-03-01'}).get_json()['contrats']
    reponse = admin.put(f"/api/employes/{fiche['id']}/contrats/{contrats[0]['id']}", {
        'heures_mensuelles': 151.67, 'date_debut': '2025-01-01', 'date_fin': '2025-03-10',
    })
    assert reponse.status_code == 409
    assert 'chevauchent' in reponse.get_json()['message']


def test_depart_puis_retour(app, admin, creer_employe):
    fiche, _ = creer_employe('alice', date_entree='2024-06-01', connecter=False)
    employe_url = f"/api/employes/{fiche['id']}"

    parti = admin.post(f'{employe_url}/depart', {'date_sortie': '2024-09-30'}).get_json()
    assert parti['date_sortie'] == '2024-09-30'
    assert parti['actif'] is False
    assert admin.get('/api/employes?statut=partis').get_json()[0]['id'] == fiche['id']
    assert admin.get('/api/employes?statut=actifs').get_json() == []

    assert admin.post(f'{employe_url}/retour', {
        'date_entree': '2024-09-15', 'heures_mensuelles': 100, 'mot_de_passe_provisoire': EMPLOYE_MDP_PROVISOIRE,
    }).status_code == 409

    revenu = admin.post(f'{employe_url}/retour', {
        'date_entree': '2025-07-01', 'heures_mensuelles': 69.33, 'mot_de_passe_provisoire': EMPLOYE_MDP_PROVISOIRE,
    }).get_json()
    assert revenu['actif'] is True
    assert revenu['date_entree'] == '2025-07-01'
    assert revenu['date_sortie'] is None
    assert len(revenu['contrats']) == 2

    session = Session(app)
    assert session.login('alice', EMPLOYE_MDP_PROVISOIRE).status_code == 200
    assert session.get('/api/auth/me').get_json()['doit_changer_mdp'] is True


def test_reinitialiser_mot_de_passe(app, admin, creer_employe):
    fiche, _ = creer_employe('alice', connecter=False)
    assert admin.post(f"/api/employes/{fiche['id']}/mot-de-passe", {'mot_de_passe_provisoire': 'nouveau-provisoire'}).status_code == 200
    session = Session(app)
    assert session.login('alice', 'nouveau-provisoire').status_code == 200
    assert session.get('/api/auth/me').get_json()['doit_changer_mdp'] is True


def test_supprimer_le_seul_contrat_refuse(admin, creer_employe):
    fiche, _ = creer_employe('alice', connecter=False)
    contrat_id = fiche['contrats'][0]['id']
    assert admin.delete(f"/api/employes/{fiche['id']}/contrats/{contrat_id}").status_code == 409
