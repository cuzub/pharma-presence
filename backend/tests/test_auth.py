from tests.conftest import EMPLOYE_MDP, EMPLOYE_MDP_PROVISOIRE, Session


def test_login_pose_un_cookie_httponly(admin):
    reponse = admin.login('pharmacienne', 'admin-mot-de-passe-test')
    cookies = reponse.headers.getlist('Set-Cookie')
    session_cookie = next(c for c in cookies if c.startswith('pharma_access_token='))
    assert 'HttpOnly' in session_cookie
    assert 'SameSite=Strict' in session_cookie
    assert 'access_token' not in reponse.get_json()
    assert admin.get('/api/auth/me').get_json()['role'] == 'admin'


def test_login_refuse_mauvais_mot_de_passe(app, admin):
    reponse = Session(app).login('pharmacienne', 'mauvais-mot-de-passe')
    assert reponse.status_code == 401
    assert reponse.get_json()['message'] == 'Identifiant ou mot de passe incorrect'


def test_requete_sans_session(app):
    assert Session(app).get('/api/mois/2025-01').status_code == 401


def test_ecriture_sans_jeton_csrf_refusee(admin, creer_employe):
    fiche, _ = creer_employe('alice', connecter=False)
    reponse = admin.client.put('/api/heures', json={'employe_id': fiche['id'], 'jour': '2025-01-02', 'minutes': 15})
    assert reponse.status_code == 401


def test_mot_de_passe_provisoire_doit_etre_change(app, creer_employe):
    creer_employe('alice', connecter=False)
    session = Session(app)
    assert session.login('alice', EMPLOYE_MDP_PROVISOIRE).status_code == 200
    assert session.get('/api/auth/me').get_json()['doit_changer_mdp'] is True

    bloque = session.get('/api/mois/2025-01')
    assert bloque.status_code == 403
    assert bloque.get_json()['code'] == 'changement_mdp_requis'

    trop_court = session.post('/api/auth/mot-de-passe', {'mot_de_passe_actuel': EMPLOYE_MDP_PROVISOIRE, 'nouveau_mot_de_passe': 'court'})
    assert trop_court.status_code == 400

    ok = session.post('/api/auth/mot-de-passe', {'mot_de_passe_actuel': EMPLOYE_MDP_PROVISOIRE, 'nouveau_mot_de_passe': EMPLOYE_MDP})
    assert ok.status_code == 200
    assert session.get('/api/mois/2025-01').status_code == 200


def test_changement_de_mot_de_passe_invalide_les_autres_sessions(app, creer_employe):
    _, session = creer_employe('alice')
    autre_poste = Session(app)
    autre_poste.login('alice', EMPLOYE_MDP)
    assert autre_poste.get('/api/auth/me').status_code == 200

    session.post('/api/auth/mot-de-passe', {'mot_de_passe_actuel': EMPLOYE_MDP, 'nouveau_mot_de_passe': 'encore-un-autre-mdp'})
    assert autre_poste.get('/api/auth/me').status_code == 401
    assert session.get('/api/auth/me').status_code == 200


def test_depart_coupe_l_acces_immediatement(app, admin, creer_employe):
    fiche, session = creer_employe('alice')
    assert session.get('/api/auth/me').status_code == 200

    assert admin.post(f"/api/employes/{fiche['id']}/depart", {'date_sortie': '2025-03-31'}).status_code == 200
    assert session.get('/api/auth/me').status_code == 401
    assert Session(app).login('alice', EMPLOYE_MDP).status_code == 401


def test_logout(admin):
    assert admin.post('/api/auth/logout').status_code == 200
    assert admin.get('/api/auth/me').status_code == 401
