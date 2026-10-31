"""Paramètres d'envoi de l'export par mail : lecture, modification et validation."""


def test_parametres_mail_vides_par_defaut(admin):
    reponse = admin.get('/api/parametres/mail')
    assert reponse.status_code == 200
    assert reponse.get_json() == {'destinataire': '', 'titre': '', 'texte': ''}


def test_modification_parametres_mail(admin):
    reponse = admin.put('/api/parametres/mail', {
        'destinataire': 'comptable@example.fr',
        'titre': 'Export {mois}',
        'texte': 'Bonjour,\n\nVeuillez trouver ci-joint l\'état préparatoire.',
    })
    assert reponse.status_code == 200
    relu = admin.get('/api/parametres/mail').get_json()
    assert relu['destinataire'] == 'comptable@example.fr'
    assert relu['titre'] == 'Export {mois}'
    assert 'ci-joint' in relu['texte']


def test_destinataire_invalide_refuse(admin):
    reponse = admin.put('/api/parametres/mail', {'destinataire': 'pas une adresse', 'titre': '', 'texte': ''})
    assert reponse.status_code == 400


def test_parametres_mail_reserves_a_l_admin(creer_employe):
    _, session_employe = creer_employe('lea', nom='Martin', prenom='Léa')
    assert session_employe.get('/api/parametres/mail').status_code == 403
    assert session_employe.put('/api/parametres/mail', {'destinataire': '', 'titre': '', 'texte': ''}).status_code == 403
