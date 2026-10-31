"""Export mensuel pour le comptable, sur un mois de février type."""

import io
from datetime import date

import pytest
from openpyxl import load_workbook

from app.extensions import db
from app.models import HeuresEnPlus

MOIS = '2025-02'


@pytest.fixture
def fevrier(admin, creer_employe, motifs):
    # Absence à cheval sur janvier et février (l'erreur « 6CP » du fichier Excel d'origine).
    laudren, _ = creer_employe('camille', nom='Laudren', prenom='Camille', heures=151.67, connecter=False)
    admin.post('/api/absences', {'employe_id': laudren['id'], 'motif_id': motifs['CP'], 'date_debut': '2025-01-28', 'date_reprise': '2025-02-03'})
    admin.put('/api/heures', {'employe_id': laudren['id'], 'jour': '2025-02-04', 'minutes': 90})
    admin.put('/api/heures', {'employe_id': laudren['id'], 'jour': '2025-02-11', 'minutes': -30})

    # Congé maternité en cours.
    gilet, _ = creer_employe('tiffany', nom='Gilet', prenom='Tiffany', connecter=False)
    admin.post('/api/absences', {'employe_id': gilet['id'], 'motif_id': motifs['MAT'], 'date_debut': '2025-02-01'})

    # Entrée en cours de mois, avec un déplacement déclaré par l'employée.
    besnard, session_besnard = creer_employe('orlane', nom='Besnard', prenom='Orlane', date_entree='2025-02-10', heures=121.33)
    deplacement = session_besnard.post('/api/deplacements', {
        'date': '2025-02-12', 'motif': 'Commande urgente', 'km': 22,
    }).get_json()

    # Partie fin janvier : ne doit pas apparaître en février.
    parti, _ = creer_employe('lucie', nom='Balbuena', prenom='Lucie', heures=121.33, connecter=False)
    admin.post(f"/api/employes/{parti['id']}/depart", {'date_sortie': '2025-01-31'})

    return {'laudren': laudren, 'gilet': gilet, 'besnard': besnard, 'deplacement_id': deplacement['id']}


def test_deplacements_declaratifs_ne_bloquent_pas_l_export(admin, fevrier):
    controles = admin.get(f'/api/exports/{MOIS}/controles').get_json()
    assert controles['bloquants'] == []
    assert any('Tiffany Gilet : absence en cours' in info for info in controles['infos'])
    assert 'Orlane Besnard : Entrée le 10/02/2025' not in controles['infos']
    assert admin.get(f'/api/exports/{MOIS}/etat-preparatoire.xlsx').status_code == 200


def test_avertissement_heures_pendant_absence(admin, fevrier):
    # Saisie antérieure à la règle de blocage : insérée directement en base.
    db.session.add(HeuresEnPlus(employe_id=fevrier['laudren']['id'], jour=date(2025, 1, 30), minutes=-45))
    db.session.commit()
    controles = admin.get('/api/exports/2025-01/controles').get_json()
    assert any('-45min le 30/01/2025' in a and 'Congés payés' in a for a in controles['avertissements'])


def test_export_excel(admin, fevrier):
    reponse = admin.get(f'/api/exports/{MOIS}/etat-preparatoire.xlsx')
    assert reponse.status_code == 200
    assert 'etat-preparatoire-2025-02.xlsx' in reponse.headers['Content-Disposition']

    wb = load_workbook(io.BytesIO(reponse.data))
    assert wb.sheetnames == ['Récapitulatif', 'Absences', 'Déplacements']

    recap = wb['Récapitulatif']
    assert recap['A1'].value == 'État préparatoire — février 2025'
    assert [c.value for c in recap[4]] == ['Nom', 'Prénom', 'Contrat (h/mois)', "Périodes d'absence", 'Km déplacements']
    lignes = [list(r) for r in recap.iter_rows(min_row=5, values_only=True)]
    par_nom = {ligne[0]: ligne for ligne in lignes}
    assert set(par_nom) == {'BESNARD', 'GILET', 'LAUDREN'}

    assert par_nom['LAUDREN'][2] == 151.67
    assert par_nom['LAUDREN'][3] == '28/01/2025 → reprise 03/02/2025 : Congés payés'
    assert par_nom['GILET'][3] == '01/02/2025 → en cours : Congé maternité'
    assert par_nom['BESNARD'][2] == 121.33
    assert par_nom['BESNARD'][4] == 22

    assert [c.value for c in wb['Déplacements'][4]] == ['Nom', 'Prénom', 'Date', 'Motif', 'Km']
    deplacements = list(wb['Déplacements'].iter_rows(min_row=5, values_only=True))
    assert len(deplacements) == 1 and deplacements[0][3] == 'Commande urgente' and deplacements[0][-1] == 22


def test_export_csv(admin, fevrier):
    recap = admin.get(f'/api/exports/{MOIS}/recap.csv')
    assert recap.status_code == 200
    contenu = recap.data.decode('utf-8')
    assert contenu.startswith('\ufeffNom;Prénom;Contrat (h/mois);Périodes d\'absence;Km déplacements')
    assert 'LAUDREN;Camille;151,67;28/01/2025 → reprise 03/02/2025 : Congés payés;' in contenu
    assert 'Heures' not in contenu and 'Entrée' not in contenu and 'Sortie' not in contenu

    assert admin.get(f'/api/exports/{MOIS}/heures.csv').status_code == 404


def test_changement_de_contrat_dans_le_mois(admin, fevrier):
    admin.post(f"/api/employes/{fevrier['laudren']['id']}/contrats", {'heures_mensuelles': 121.33, 'date_debut': '2025-02-15'})
    controles = admin.get(f'/api/exports/{MOIS}/controles').get_json()
    assert any('changement de contrat' in info for info in controles['infos'])
    assert not any('Laudren : Entrée' in info or 'Laudren : Sortie' in info for info in controles['infos'])

    contenu = admin.get(f'/api/exports/{MOIS}/recap.csv').data.decode('utf-8')
    assert 'LAUDREN;Camille;151,67 (au 14/02/2025) puis 121,33 (du 15/02/2025);' in contenu


def test_mois_invalide(admin):
    assert admin.get('/api/mois/2025-13').status_code == 400
    assert admin.get('/api/exports/abc/controles').status_code == 400


def test_textes_saisis_jamais_interpretes_comme_formules(admin, creer_employe):
    fiche, session = creer_employe('mallory', nom='=HYPERLINK("http://x")', prenom='Eve')
    deplacement = session.post('/api/deplacements', {
        'date': '2025-02-12', 'motif': '=cmd|calc', 'km': 5,
    }).get_json()

    wb = load_workbook(io.BytesIO(admin.get(f'/api/exports/{MOIS}/etat-preparatoire.xlsx').data))
    ligne = next(wb['Déplacements'].iter_rows(min_row=5))
    assert [ligne[i].data_type for i in (0, 1, 3)] == ['s'] * 3
    assert ligne[3].value == '=cmd|calc'

    contenu = admin.get(f'/api/exports/{MOIS}/recap.csv').data.decode('utf-8')
    assert '"\'=HYPERLINK(""HTTP://X"")";Eve;' in contenu
