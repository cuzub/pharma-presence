"""Déplacements déclaratifs : motifs (km automatiques), « Autre », historique figé, fenêtre de modification."""

from datetime import date

import pytest

from app.services.fenetre import modifiable_par_employe


def _creer_motif(admin, libelle='Domitis', km=2, **extra):
    reponse = admin.post('/api/deplacements/motifs', {'libelle': libelle, 'km': km, **extra})
    assert reponse.status_code == 201, reponse.get_json()
    return reponse.get_json()


def test_un_seul_deplacement_par_jour_et_par_employe(admin, creer_employe):
    domitis = _creer_motif(admin)
    _, session = creer_employe('alice')
    trajet = {'date': '2025-01-15', 'motif_deplacement_id': domitis['id']}
    premier = session.post('/api/deplacements', trajet)
    assert premier.status_code == 201, premier.get_json()

    doublon = session.post('/api/deplacements', trajet)
    assert doublon.status_code == 409
    assert session.post('/api/deplacements', {**trajet, 'date': '2025-01-16'}).status_code == 201

    # Modifier le déplacement existant reste possible (il n'est pas son propre doublon).
    assert session.put(f"/api/deplacements/{premier.get_json()['id']}", trajet).status_code == 200


def test_admin_gere_les_motifs(admin, creer_employe):
    domitis = _creer_motif(admin)
    lcl = _creer_motif(admin, 'LCL', 30)
    assert lcl['ordre'] > domitis['ordre']

    assert admin.post('/api/deplacements/motifs', {'libelle': 'domitis', 'km': 3}).status_code == 409
    assert admin.post('/api/deplacements/motifs', {'libelle': 'Autre', 'km': 3}).status_code == 409
    assert admin.post('/api/deplacements/motifs', {'libelle': 'Orgères', 'km': 0}).status_code == 400

    modifie = admin.put(f"/api/deplacements/motifs/{domitis['id']}", {'libelle': 'Domitis', 'km': 2.5, 'actif': False})
    assert modifie.get_json() == {**domitis, 'km': 2.5, 'actif': False}

    _, session = creer_employe('alice')
    assert [m['libelle'] for m in session.get('/api/deplacements/motifs').get_json()] == ['Domitis', 'LCL']
    assert session.post('/api/deplacements/motifs', {'libelle': 'X', 'km': 1}).status_code == 403
    assert session.put(f"/api/deplacements/motifs/{lcl['id']}", {'libelle': 'X', 'km': 1}).status_code == 403


def test_km_renseignes_depuis_le_motif(admin, creer_employe):
    domitis = _creer_motif(admin)
    _, session = creer_employe('alice')

    # Les km envoyés par le client sont ignorés : seuls ceux du motif comptent.
    cree = session.post('/api/deplacements', {'date': '2025-01-15', 'motif_deplacement_id': domitis['id'], 'km': 999})
    assert cree.status_code == 201, cree.get_json()
    assert cree.get_json()['motif'] == 'Domitis'
    assert cree.get_json()['km'] == 2
    assert cree.get_json()['motif_deplacement_id'] == domitis['id']


def test_motif_autre_avec_precision_et_km_libres(admin, creer_employe):
    _, session = creer_employe('alice')
    assert session.post('/api/deplacements', {'date': '2025-01-15', 'km': 12}).status_code == 400
    assert session.post('/api/deplacements', {'date': '2025-01-15', 'motif': 'Pharmacie de Chartres'}).status_code == 400

    cree = session.post('/api/deplacements', {
        'date': '2025-01-15', 'motif_deplacement_id': None, 'motif': 'Pharmacie de Chartres', 'km': 12.5,
    }).get_json()
    assert cree['motif_deplacement_id'] is None
    assert cree['motif'] == 'Pharmacie de Chartres'
    assert cree['km'] == 12.5


def test_motif_invalide_ou_desactive_refuse(admin, creer_employe):
    ancien = _creer_motif(admin, 'Ancien', 4, actif=False)
    _, session = creer_employe('alice')
    assert session.post('/api/deplacements', {'date': '2025-01-15', 'motif_deplacement_id': 999}).status_code == 400
    assert session.post('/api/deplacements', {'date': '2025-01-15', 'motif_deplacement_id': 'x'}).status_code == 400
    assert session.post('/api/deplacements', {'date': '2025-01-15', 'motif_deplacement_id': ancien['id']}).status_code == 400


def test_historique_fige_quand_le_motif_change(admin, creer_employe):
    domitis = _creer_motif(admin)
    _, session = creer_employe('alice')
    ancien = session.post('/api/deplacements', {'date': '2025-01-15', 'motif_deplacement_id': domitis['id']}).get_json()

    admin.put(f"/api/deplacements/motifs/{domitis['id']}", {'libelle': 'Domitis Chartres', 'km': 3, 'actif': False})

    # Déplacement existant : inchangé, et reste modifiable (changement de date) malgré le motif désactivé.
    modifie = session.put(f"/api/deplacements/{ancien['id']}", {'date': '2025-01-16', 'motif_deplacement_id': domitis['id']})
    assert modifie.status_code == 200, modifie.get_json()
    assert (modifie.get_json()['date'], modifie.get_json()['motif'], modifie.get_json()['km']) == ('2025-01-16', 'Domitis', 2)

    # Réactivé : un nouveau déplacement prend la nouvelle distance.
    admin.put(f"/api/deplacements/motifs/{domitis['id']}", {'libelle': 'Domitis Chartres', 'km': 3})
    nouveau = session.post('/api/deplacements', {'date': '2025-01-17', 'motif_deplacement_id': domitis['id']}).get_json()
    assert (nouveau['motif'], nouveau['km']) == ('Domitis Chartres', 3)


def test_passer_d_un_motif_a_autre_et_inversement(admin, creer_employe):
    lcl = _creer_motif(admin, 'LCL', 30)
    _, session = creer_employe('alice')
    deplacement = session.post('/api/deplacements', {'date': '2025-01-15', 'motif': 'Grossiste', 'km': 8}).get_json()

    vers_motif = session.put(f"/api/deplacements/{deplacement['id']}", {'date': '2025-01-15', 'motif_deplacement_id': lcl['id']}).get_json()
    assert (vers_motif['motif_deplacement_id'], vers_motif['motif'], vers_motif['km']) == (lcl['id'], 'LCL', 30)

    vers_autre = session.put(f"/api/deplacements/{deplacement['id']}", {'date': '2025-01-15', 'motif_deplacement_id': None, 'motif': 'Grossiste', 'km': 8}).get_json()
    assert (vers_autre['motif_deplacement_id'], vers_autre['motif'], vers_autre['km']) == (None, 'Grossiste', 8)


def test_mois_admin_inclut_les_deplacements(admin, creer_employe):
    fiche, session = creer_employe('alice')
    session.post('/api/deplacements', {'date': '2025-01-15', 'motif': 'Grossiste', 'km': 8})
    employe = next(e for e in admin.get('/api/mois/2025-01').get_json()['employes'] if e['id'] == fiche['id'])
    assert [(d['date'], d['motif']) for d in employe['deplacements']] == [('2025-01-15', 'Grossiste')]


@pytest.mark.parametrize('reference, jour, attendu', [
    (date(2025, 3, 5), date(2025, 2, 28), True),    # mois précédent, jusqu'au 5 inclus
    (date(2025, 3, 6), date(2025, 2, 28), False),   # trop tard
    (date(2025, 3, 6), date(2025, 3, 31), True),    # mois en cours, même dans le futur
    (date(2025, 3, 1), date(2025, 1, 31), False),   # deux mois avant
    (date(2025, 3, 1), date(2025, 4, 1), False),    # mois suivant
    (date(2025, 1, 3), date(2024, 12, 15), True),   # passage d'année
])
def test_fenetre_de_modification_employe(reference, jour, attendu):
    assert modifiable_par_employe(jour, reference) is attendu


def test_employe_bloque_hors_fenetre_admin_jamais(admin, creer_employe, aujourdhui):
    fiche, session = creer_employe('alice')
    trajet = {'date': '2025-01-15', 'motif': 'Grossiste', 'km': 8}
    deplacement_id = session.post('/api/deplacements', trajet).get_json()['id']

    aujourdhui['date'] = date(2025, 2, 6)
    assert session.post('/api/deplacements', trajet).status_code == 403
    assert session.put(f'/api/deplacements/{deplacement_id}', {**trajet, 'km': 9}).status_code == 403
    assert session.delete(f'/api/deplacements/{deplacement_id}').status_code == 403
    # Déplacer un déplacement récent vers une date verrouillée : refusé aussi.
    recent_id = session.post('/api/deplacements', {**trajet, 'date': '2025-02-04'}).get_json()['id']
    assert session.put(f'/api/deplacements/{recent_id}', trajet).status_code == 403

    assert admin.put(f'/api/deplacements/{deplacement_id}', {**trajet, 'km': 9}).get_json()['km'] == 9
    assert admin.post('/api/deplacements', {**trajet, 'employe_id': fiche['id'], 'date': '2024-06-01'}).status_code == 201
    assert admin.delete(f'/api/deplacements/{deplacement_id}').status_code == 204
