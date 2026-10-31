"""Journal des modifications : qui a créé / modifié / supprimé quoi, et quand."""


def _journal(admin, **filtres):
    reponse = admin.get('/api/journal', query_string=filtres)
    assert reponse.status_code == 200, reponse.get_json()
    return reponse.get_json()


def test_deplacement_trace_creation_modification_suppression(admin, creer_employe):
    fiche, session = creer_employe('alice')
    trajet = {'date': '2025-01-15', 'motif': 'Grossiste', 'km': 8}
    deplacement_id = session.post('/api/deplacements', trajet).get_json()['id']
    admin.put(f'/api/deplacements/{deplacement_id}', {**trajet, 'km': 10})
    # Enregistrement sans changement : pas de ligne.
    admin.put(f'/api/deplacements/{deplacement_id}', {**trajet, 'km': 10})
    session.delete(f'/api/deplacements/{deplacement_id}')

    lignes = _journal(admin)['lignes']
    assert [(l['action'], l['auteur_role'], l['auteur_identifiant']) for l in lignes] == [
        ('suppression', 'employe', 'alice'),
        ('modification', 'admin', 'pharmacienne'),
        ('creation', 'employe', 'alice'),
    ]
    assert all(l['type'] == 'deplacement' and l['employe_id'] == fiche['id'] and l['objet_id'] == deplacement_id for l in lignes)
    assert lignes[2]['avant'] is None and lignes[2]['apres'] == {'date': '2025-01-15', 'motif': 'Grossiste', 'km': 8}
    assert lignes[1]['avant']['km'] == 8 and lignes[1]['apres']['km'] == 10
    assert lignes[0]['avant']['km'] == 10 and lignes[0]['apres'] is None


def test_heures_et_absences_tracees(admin, creer_employe, motifs):
    fiche, _ = creer_employe('alice', connecter=False)
    admin.put('/api/heures', {'employe_id': fiche['id'], 'jour': '2025-01-10', 'minutes': 15})
    admin.put('/api/heures', {'employe_id': fiche['id'], 'jour': '2025-01-10', 'minutes': -30})
    admin.put('/api/heures', {'employe_id': fiche['id'], 'jour': '2025-01-10', 'minutes': 0})
    # Effacer un jour vide : rien à tracer.
    admin.put('/api/heures', {'employe_id': fiche['id'], 'jour': '2025-01-11', 'minutes': 0})

    absence = {'employe_id': fiche['id'], 'motif_id': motifs['MAL'], 'date_debut': '2025-01-20'}
    absence_id = admin.post('/api/absences', absence).get_json()['id']
    admin.put(f'/api/absences/{absence_id}', {**absence, 'date_reprise': '2025-01-23'})
    admin.delete(f'/api/absences/{absence_id}')

    heures = _journal(admin, type='heures')['lignes']
    assert [(l['action'], l['avant'], l['apres']) for l in heures] == [
        ('suppression', {'jour': '2025-01-10', 'minutes': -30}, None),
        ('modification', {'jour': '2025-01-10', 'minutes': 15}, {'jour': '2025-01-10', 'minutes': -30}),
        ('creation', None, {'jour': '2025-01-10', 'minutes': 15}),
    ]
    absences = _journal(admin, type='absence')['lignes']
    assert [l['action'] for l in absences] == ['suppression', 'modification', 'creation']
    assert absences[1]['avant']['date_reprise'] is None and absences[1]['apres']['date_reprise'] == '2025-01-23'
    assert absences[2]['apres']['motif'] == 'Maladie'


def test_filtres_et_pagination(admin, creer_employe):
    alice, session_alice = creer_employe('alice')
    bruno, _ = creer_employe('bruno', connecter=False)
    session_alice.post('/api/deplacements', {'date': '2025-01-15', 'motif': 'A', 'km': 1})
    admin.post('/api/deplacements', {'employe_id': bruno['id'], 'date': '2025-01-15', 'motif': 'B', 'km': 2})
    admin.put('/api/heures', {'employe_id': alice['id'], 'jour': '2025-01-10', 'minutes': 15})

    assert _journal(admin)['total'] == 3
    assert {l['employe_id'] for l in _journal(admin, employe_id=bruno['id'])['lignes']} == {bruno['id']}
    assert [l['auteur_identifiant'] for l in _journal(admin, auteur='employe')['lignes']] == ['alice']
    assert _journal(admin, type='deplacement')['total'] == 2

    from datetime import datetime
    mois_courant = datetime.now().strftime('%Y-%m')
    assert _journal(admin, mois=mois_courant)['total'] == 3
    assert _journal(admin, mois='2020-01')['total'] == 0

    page = _journal(admin, par_page=2, page=2)
    assert page['total'] == 3 and len(page['lignes']) == 1

    assert admin.get('/api/journal?type=x').status_code == 400
    assert admin.get('/api/journal?auteur=x').status_code == 400


def test_journal_en_lecture_seule(admin):
    for methode in ('post', 'put', 'delete'):
        assert getattr(admin, methode)('/api/journal').status_code == 405
