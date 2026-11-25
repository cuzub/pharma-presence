"""Planning de présence : trames semaine 1 / semaine 2, exceptions à la journée, totaux, couleur, cloisonnement."""

import pytest

JOURNEE = {'matin': ['09:00', '12:30'], 'apres_midi': ['14:30', '19:30']}
REPOS = {'matin': None, 'apres_midi': None}
MATIN = {'matin': ['09:00', '12:30'], 'apres_midi': None}


def _horaires(semaine_1, semaine_2=None):
    return {'1': semaine_1, '2': semaine_2 or semaine_1}


@pytest.fixture
def alice(creer_employe):
    return creer_employe('alice', nom='MARTIN')


def _creer_trame(session, horaires, date_debut='2025-01-01', **titulaire):
    return session.post('/api/planning/trames', {'date_debut': date_debut, 'horaires': horaires, **titulaire})


def _ligne(session, mois, employe_id):
    return next(e for e in session.get(f'/api/mois/{mois}').get_json()['employes'] if e['id'] == employe_id)


def test_semaines_paires_et_impaires_et_total_hebdomadaire(admin, alice):
    fiche, _ = alice
    # Semaine 1 (ISO impaire) : lundi seul ; semaine 2 (ISO paire) : lundi à samedi matin.
    semaine_1 = [JOURNEE] + [REPOS] * 5
    semaine_2 = [JOURNEE] * 5 + [MATIN]
    assert _creer_trame(admin, _horaires(semaine_1, semaine_2), employe_id=fiche['id']).status_code == 201

    ligne = _ligne(admin, '2025-02', fiche['id'])
    # 3 février 2025 : semaine ISO 6 (paire) ; 10 février : semaine 7 (impaire).
    assert ligne['planning']['2025-02-03'] == {**JOURNEE, 'exception': False}
    assert ligne['planning']['2025-02-08'] == {**MATIN, 'exception': False}
    assert '2025-02-11' not in ligne['planning']
    assert ligne['totaux_semaines']['2025-02-03'] == 5 * 510 + 210
    assert ligne['totaux_semaines']['2025-02-10'] == 510
    # Semaine à cheval sur janvier : elle commence le lundi 27 janvier et compte en entier.
    assert ligne['totaux_semaines']['2025-01-27'] == 510
    assert ligne['couleur'].startswith('#')


def test_absence_non_deduite_du_total_de_la_semaine(admin, alice, motifs):
    fiche, _ = alice
    _creer_trame(admin, _horaires([JOURNEE] * 5 + [MATIN]), employe_id=fiche['id'])
    reponse = admin.post('/api/absences', {'employe_id': fiche['id'], 'motif_id': motifs['CP'], 'date_debut': '2025-02-03', 'date_reprise': '2025-02-05'})
    assert reponse.status_code == 201, reponse.get_json()
    assert _ligne(admin, '2025-02', fiche['id'])['totaux_semaines']['2025-02-03'] == 5 * 510 + 210


def test_nouvelle_trame_a_partir_d_une_date(admin, alice):
    fiche, _ = alice
    _creer_trame(admin, _horaires([JOURNEE] * 5 + [MATIN]), employe_id=fiche['id'])
    _creer_trame(admin, _horaires([MATIN] * 6), date_debut='2025-02-12', employe_id=fiche['id'])
    planning = _ligne(admin, '2025-02', fiche['id'])['planning']
    assert planning['2025-02-11']['apres_midi'] == ['14:30', '19:30']
    assert planning['2025-02-12']['apres_midi'] is None
    assert _creer_trame(admin, _horaires([MATIN] * 6), date_debut='2025-02-12', employe_id=fiche['id']).status_code == 409


def test_exception_remplace_la_trame_ce_jour_la(admin, alice):
    fiche, _ = alice
    _creer_trame(admin, _horaires([JOURNEE] * 5 + [MATIN]), employe_id=fiche['id'])
    reponse = admin.put('/api/planning/exceptions', {
        'employe_id': fiche['id'], 'jour': '2025-02-04', 'matin': ['10:00', '12:30'], 'apres_midi': None,
    })
    assert reponse.status_code == 200, reponse.get_json()
    admin.put('/api/planning/exceptions', {'employe_id': fiche['id'], 'jour': '2025-02-05', 'matin': None, 'apres_midi': None})

    ligne = _ligne(admin, '2025-02', fiche['id'])
    assert ligne['planning']['2025-02-04'] == {'matin': ['10:00', '12:30'], 'apres_midi': None, 'exception': True}
    assert ligne['planning']['2025-02-05'] == {'matin': None, 'apres_midi': None, 'exception': True}
    assert ligne['totaux_semaines']['2025-02-03'] == 3 * 510 + 150 + 210

    assert admin.delete(f'/api/planning/exceptions?employe_id={fiche["id"]}&jour=2025-02-04').status_code == 204
    assert _ligne(admin, '2025-02', fiche['id'])['planning']['2025-02-04']['exception'] is False


@pytest.mark.parametrize('jour, matin, apres_midi', [
    ('2025-02-04', ['08:30', '12:30'], None),       # avant l'ouverture
    ('2025-02-04', None, ['12:45', '19:30']),       # pendant la pause
    ('2025-02-04', None, ['14:30', '20:00']),       # après la fermeture
    ('2025-02-04', ['11:00', '10:00'], None),       # fin avant début
    ('2025-02-04', ['09:02', '12:00'], None),       # pas de 5 minutes
    ('2025-02-08', None, ['14:30', '19:30']),       # samedi après-midi
    ('2025-02-09', ['09:00', '12:30'], None),       # dimanche
])
def test_horaires_invalides_refuses(admin, alice, jour, matin, apres_midi):
    fiche, _ = alice
    reponse = admin.put('/api/planning/exceptions', {'employe_id': fiche['id'], 'jour': jour, 'matin': matin, 'apres_midi': apres_midi})
    assert reponse.status_code == 400


def test_trame_incomplete_refusee(admin, alice):
    fiche, _ = alice
    assert _creer_trame(admin, {'1': [JOURNEE] * 5, '2': [JOURNEE] * 6}, employe_id=fiche['id']).status_code == 400


def test_planning_de_l_admin_cyan_et_proprietaire(app, admin):
    from app.extensions import db
    from app.models import Utilisateur
    from tests.conftest import ADMIN_MDP, Session

    moi = admin.get('/api/auth/me').get_json()['id']
    assert _creer_trame(admin, _horaires([JOURNEE] * 5 + [MATIN])).status_code == 201
    ligne = next(a for a in admin.get('/api/mois/2025-02').get_json()['admins'] if a['id'] == moi)
    assert ligne['couleur'] == '#00bcd4'
    assert ligne['planning']['2025-02-08'] == {**MATIN, 'exception': False}

    associe = Utilisateur(identifiant='associe', role=Utilisateur.ROLE_ADMIN)
    associe.definir_mot_de_passe(ADMIN_MDP, provisoire=False)
    db.session.add(associe)
    db.session.commit()
    autre = Session(app)
    autre.login('associe', ADMIN_MDP)
    trame_id = admin.get('/api/planning/trames').get_json()['trames'][0]['id']
    assert autre.put(f'/api/planning/trames/{trame_id}', {'date_debut': '2025-01-01', 'horaires': _horaires([REPOS] * 6)}).status_code == 403
    assert autre.put('/api/planning/exceptions', {'utilisateur_id': moi, 'jour': '2025-02-04'}).status_code == 403


def test_employe_voit_son_planning_sans_pouvoir_le_modifier(admin, alice, creer_employe):
    fiche, session = alice
    bruno, _ = creer_employe('bruno', nom='DURAND', connecter=False)
    _creer_trame(admin, _horaires([JOURNEE] * 5 + [MATIN]), employe_id=fiche['id'])

    donnees = session.get('/api/mois/2025-02').get_json()
    assert [e['id'] for e in donnees['employes']] == [fiche['id']]
    assert donnees['employes'][0]['planning']['2025-02-03']['matin'] == ['09:00', '12:30']
    assert donnees['admins'] == []
    assert session.get(f'/api/planning/trames?employe_id={bruno["id"]}').status_code == 403
    assert _creer_trame(session, _horaires([REPOS] * 6), employe_id=fiche['id']).status_code == 403
    assert session.put('/api/planning/exceptions', {'employe_id': fiche['id'], 'jour': '2025-02-04'}).status_code == 403


def test_couleur_de_l_employe(admin, alice, creer_employe):
    fiche, _ = alice
    bruno, _ = creer_employe('bruno', nom='DURAND', connecter=False)
    assert fiche['couleur'] != bruno['couleur']
    url = f'/api/employes/{fiche["id"]}'
    assert admin.put(url, {'nom': 'MARTIN', 'prenom': 'Alice', 'couleur': '#123ABC'}).get_json()['couleur'] == '#123abc'
    assert admin.put(url, {'nom': 'MARTIN', 'prenom': 'Alice', 'couleur': 'rouge'}).status_code == 400


def test_planning_masque_hors_contrat(admin, creer_employe):
    fiche, _ = creer_employe('chloe', nom='PETIT', date_entree='2025-02-05', connecter=False)
    _creer_trame(admin, _horaires([JOURNEE] * 5 + [MATIN]), employe_id=fiche['id'])
    ligne = _ligne(admin, '2025-02', fiche['id'])
    assert '2025-02-04' not in ligne['planning']
    assert ligne['totaux_semaines']['2025-02-03'] == 3 * 510 + 210
