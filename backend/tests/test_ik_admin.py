"""Indemnités kilométriques de l'admin : saisie cloisonnée, journal, exclusions et export annuel."""

import io
import re
import zipfile

import pytest
from openpyxl import load_workbook

from app.extensions import db
from app.models import Utilisateur
from tests.conftest import ADMIN_MDP, Session


@pytest.fixture
def autre_admin(app):
    utilisateur = Utilisateur(identifiant='associe', role=Utilisateur.ROLE_ADMIN)
    utilisateur.definir_mot_de_passe(ADMIN_MDP, provisoire=False)
    db.session.add(utilisateur)
    db.session.commit()
    session = Session(app)
    assert session.login('associe', ADMIN_MDP).status_code == 200
    return session


@pytest.fixture
def moi(admin):
    return admin.get('/api/auth/me').get_json()['id']


def _trajet_admin(session, utilisateur_id, date, km=12, motif='Banque'):
    return session.post('/api/deplacements', {
        'utilisateur_id': utilisateur_id, 'date': date, 'motif': motif, 'km': km,
    })


def _admins(session, mois):
    return session.get(f'/api/mois/{mois}').get_json()['admins']


# --- Saisie (section 3.5) ---------------------------------------------------

def test_admin_cree_son_propre_trajet_sans_employe(admin, moi):
    reponse = _trajet_admin(admin, moi, '2025-02-12')
    assert reponse.status_code == 201, reponse.get_json()
    assert reponse.get_json()['utilisateur_id'] == moi
    assert reponse.get_json()['employe_id'] is None

    mois = admin.get('/api/mois/2025-02').get_json()
    assert mois['employes'] == []
    ligne, = mois['admins']
    assert ligne['est_moi'] is True
    assert ligne['total_km'] == 12


def test_un_seul_trajet_admin_par_jour(admin, moi):
    assert _trajet_admin(admin, moi, '2025-02-12').status_code == 201
    assert _trajet_admin(admin, moi, '2025-02-12', km=5).status_code == 409


def test_admin_ne_peut_pas_saisir_pour_un_autre_admin(admin, autre_admin, moi):
    autre_id = autre_admin.get('/api/auth/me').get_json()['id']
    assert _trajet_admin(admin, autre_id, '2025-02-12').status_code == 403

    reponse = _trajet_admin(autre_admin, autre_id, '2025-02-13')
    assert reponse.status_code == 201
    trajet = reponse.get_json()['id']
    assert admin.put(f'/api/deplacements/{trajet}', {'km': 3, 'motif': 'Hack', 'date': '2025-02-13'}).status_code == 403
    assert admin.delete(f'/api/deplacements/{trajet}').status_code == 403

    vus = {l['nom']: l['est_moi'] for l in _admins(autre_admin, '2025-02')}
    assert vus == {'associe': True, 'pharmacienne': False}


def test_employe_qui_envoie_utilisateur_id_saisit_a_son_nom(admin, creer_employe, moi):
    fiche, session = creer_employe('alice')
    motif = admin.post('/api/deplacements/motifs', {'libelle': 'Domitis', 'km': 2}).get_json()

    reponse = session.post('/api/deplacements', {
        'utilisateur_id': moi, 'date': '2025-02-03', 'motif_deplacement_id': motif['id'],
    })
    assert reponse.status_code == 201, reponse.get_json()
    assert reponse.get_json()['employe_id'] == fiche['id']
    assert reponse.get_json()['utilisateur_id'] is None

    assert session.get('/api/mois/2025-02').get_json()['admins'] == []


def test_employe_ne_modifie_pas_un_trajet_admin(admin, creer_employe, moi):
    _, session = creer_employe('alice')
    trajet = _trajet_admin(admin, moi, '2025-02-12').get_json()['id']
    assert session.put(f'/api/deplacements/{trajet}', {'km': 1, 'motif': 'X', 'date': '2025-02-12'}).status_code == 404
    assert session.delete(f'/api/deplacements/{trajet}').status_code == 404


def test_admin_desactive_present_seulement_s_il_a_des_trajets(admin, autre_admin, app):
    autre_id = autre_admin.get('/api/auth/me').get_json()['id']
    utilisateur = db.session.get(Utilisateur, autre_id)
    utilisateur.actif = False
    db.session.commit()
    assert 'associe' not in [l['nom'] for l in _admins(admin, '2025-02')]

    utilisateur.actif = True
    db.session.commit()
    _trajet_admin(autre_admin, autre_id, '2025-02-12')
    utilisateur.actif = False
    db.session.commit()
    assert 'associe' in [l['nom'] for l in _admins(admin, '2025-02')]


def test_journal_trajet_admin_et_renommage(admin, moi):
    _trajet_admin(admin, moi, '2025-02-12')
    ligne, = admin.get('/api/journal').get_json()['lignes']
    assert ligne['type'] == 'deplacement'
    assert ligne['employe_id'] is None
    assert ligne['admin_concerne_nom'] == 'pharmacienne'

    assert admin.put('/api/parametres/ik', {'coefficient': '0,636', 'nom_affiche': 'Elise'}).status_code == 200
    ligne, = admin.get('/api/journal').get_json()['lignes']
    assert ligne['admin_concerne_nom'] == 'Elise'


def test_exclusions_etat_preparatoire_csv_controles(admin, creer_employe, moi):
    fiche, _ = creer_employe('alice')
    motif = admin.post('/api/deplacements/motifs', {'libelle': 'Domitis', 'km': 22}).get_json()
    assert admin.post('/api/deplacements', {
        'employe_id': fiche['id'], 'date': '2025-02-10', 'motif_deplacement_id': motif['id'],
    }).status_code == 201
    assert _trajet_admin(admin, moi, '2025-02-12', km=30, motif='Banque').status_code == 201

    classeur = load_workbook(io.BytesIO(admin.get('/api/exports/2025-02/etat-preparatoire.xlsx').data))
    valeurs_deplacements = [c for ligne in classeur['Déplacements'].iter_rows(values_only=True) for c in ligne]
    assert 22 in valeurs_deplacements
    assert 30 not in valeurs_deplacements
    valeurs_recap = [c for ligne in classeur['Récapitulatif'].iter_rows(values_only=True) for c in ligne]
    assert 'pharmacienne' not in valeurs_recap

    assert 'pharmacienne' not in admin.get('/api/exports/2025-02/controles').get_data(as_text=True)
    assert 'pharmacienne' not in admin.get('/api/exports/2025-02/recap.csv').get_data(as_text=True)


def test_liste_deplacements_et_statistiques_ignorent_les_trajets_admin(admin, moi):
    avant = admin.get('/api/statistiques/2025').get_json()

    _trajet_admin(admin, moi, '2025-02-12')

    trajets = admin.get('/api/deplacements').get_json()
    assert all(t['utilisateur_id'] is None for t in trajets)
    assert admin.get('/api/statistiques/2025').get_json() == avant


# --- Export annuel IK (section 4) -------------------------------------------

def _definir_coefficient(admin, valeur='0,636'):
    assert admin.put('/api/parametres/ik', {'coefficient': valeur}).status_code == 200


def test_export_ik_sans_coefficient_renvoie_409(admin):
    reponse = admin.get('/api/exports/ik/2025.xlsx')
    assert reponse.status_code == 409
    assert reponse.get_json()['code'] == 'coefficient_ik_manquant'


def test_export_ik_calcule_les_montants_par_mois(admin, creer_employe, moi):
    _definir_coefficient(admin)
    for date, km in [('2024-12-31', 10), ('2025-01-01', 30), ('2025-01-15', 2),
                     ('2025-03-12', 5.5), ('2025-12-31', 1)]:
        assert _trajet_admin(admin, moi, date, km=km).status_code == 201, date

    fiche, _ = creer_employe('alice')
    motif = admin.post('/api/deplacements/motifs', {'libelle': 'Long', 'km': 100}).get_json()
    assert admin.post('/api/deplacements', {
        'employe_id': fiche['id'], 'date': '2025-01-20', 'motif_deplacement_id': motif['id'],
    }).status_code == 201

    reponse = admin.get('/api/exports/ik/2025.xlsx')
    assert reponse.status_code == 200
    assert 'indemnites-km-2025.xlsx' in reponse.headers['Content-Disposition']
    classeur = load_workbook(io.BytesIO(reponse.data))
    assert classeur.sheetnames == ['IK 2025']
    feuille = classeur['IK 2025']
    assert feuille['A1'].value == 'Indemnités kilométriques — pharmacienne — 2025'
    assert '0,636' in feuille['A3'].value
    assert [c.value for c in feuille[4]] == ['Mois', 'Kilomètres', 'Montant (€)']

    lignes = {r[0].value: (r[1].value, r[2].value) for r in feuille.iter_rows(min_row=5, max_row=17)}
    assert lignes['Janvier 2025'][0] == pytest.approx(32.0)
    assert lignes['Janvier 2025'][1] == pytest.approx(20.35)
    assert lignes['Février 2025'] == (0.0, 0.0)
    assert lignes['Mars 2025'][0] == pytest.approx(5.5)
    assert lignes['Mars 2025'][1] == pytest.approx(3.50)
    assert lignes['Décembre 2025'][1] == pytest.approx(0.64)
    assert lignes['Total'][0] == pytest.approx(38.5)
    assert lignes['Total'][1] == pytest.approx(24.49)
    vue = re.search(rb'<sheetViews>.*?</sheetViews>', zipfile.ZipFile(io.BytesIO(reponse.data)).read('xl/worksheets/sheet1.xml')).group(0)
    assert vue.count(b'<selection') == 1, 'volets figés déclarés plusieurs fois : Excel répare le fichier'


def test_export_ik_validation_et_droits(admin, creer_employe):
    _definir_coefficient(admin)
    assert admin.get('/api/exports/ik/1999.xlsx').status_code == 400
    _, session = creer_employe('alice')
    assert session.get('/api/exports/ik/2025.xlsx').status_code == 403
