"""Données consolidées d'un mois : base du tableau du mois, des contrôles et de l'export comptable."""

from collections import defaultdict
from datetime import timedelta

from sqlalchemy import or_

from app.models import Absence, Deplacement, Employe, HeuresEnPlus, JourFermeture
from app.utils import format_date_fr

MOIS_FR = [
    'janvier', 'février', 'mars', 'avril', 'mai', 'juin',
    'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre',
]


def libelle_mois(debut):
    return f'{MOIS_FR[debut.month - 1]} {debut.year}'


def format_nombre_fr(valeur):
    texte = f'{valeur:.2f}'.rstrip('0').rstrip('.')
    return texte.replace('.', ',') if texte else '0'


def format_minutes(minutes):
    """+90 → « +1h30 », -30 → « -30min »."""
    signe = '-' if minutes < 0 else '+'
    heures, reste = divmod(abs(minutes), 60)
    if not heures:
        return f'{signe}{reste}min'
    return f'{signe}{heures}h{reste:02d}' if reste else f'{signe}{heures}h'


def texte_absence(absence):
    reprise = f'reprise {format_date_fr(absence.date_reprise)}' if absence.date_reprise else 'en cours'
    return f'{format_date_fr(absence.date_debut)} → {reprise} : {absence.motif.libelle}'


def _texte_contrats(contrats, debut, fin):
    if len(contrats) == 1:
        return format_nombre_fr(contrats[0].heures)
    morceaux = []
    for contrat in contrats:
        bornes = []
        if contrat.date_debut > debut:
            bornes.append(f'du {format_date_fr(contrat.date_debut)}')
        if contrat.date_fin and contrat.date_fin < fin:
            bornes.append(f'au {format_date_fr(contrat.date_fin)}')
        morceaux.append(f"{format_nombre_fr(contrat.heures)} ({' '.join(bornes)})" if bornes else format_nombre_fr(contrat.heures))
    return ' puis '.join(morceaux)


def _mouvements(employe, debut, fin):
    """Entrées et sorties réelles dans le mois (un avenant n'est ni une entrée ni une sortie)."""
    mouvements = []
    contrats = employe.contrats
    for index, contrat in enumerate(contrats):
        precedent = contrats[index - 1] if index > 0 else None
        suivant = contrats[index + 1] if index + 1 < len(contrats) else None
        continuite_avant = precedent and precedent.date_fin and (contrat.date_debut - precedent.date_fin).days == 1
        continuite_apres = suivant and contrat.date_fin and (suivant.date_debut - contrat.date_fin).days == 1
        if debut <= contrat.date_debut <= fin and not continuite_avant:
            mouvements.append(f'Entrée le {format_date_fr(contrat.date_debut)}')
        if contrat.date_fin and debut <= contrat.date_fin <= fin and not continuite_apres:
            mouvements.append(f'Sortie le {format_date_fr(contrat.date_fin)}')
    return mouvements


def donnees_mois(debut, fin, employe_id=None):
    """Retourne la liste des employés concernés par le mois avec toutes leurs saisies."""
    absences_q = Absence.query.filter(
        Absence.date_debut <= fin, or_(Absence.date_reprise.is_(None), Absence.date_reprise > debut)
    )
    heures_q = HeuresEnPlus.query.filter(HeuresEnPlus.jour.between(debut, fin))
    deplacements_q = Deplacement.query.filter(Deplacement.date.between(debut, fin))
    employes_q = Employe.query
    if employe_id is not None:
        absences_q = absences_q.filter(Absence.employe_id == employe_id)
        heures_q = heures_q.filter(HeuresEnPlus.employe_id == employe_id)
        deplacements_q = deplacements_q.filter(Deplacement.employe_id == employe_id)
        employes_q = employes_q.filter(Employe.id == employe_id)

    absences = defaultdict(list)
    for absence in absences_q.order_by(Absence.date_debut).all():
        absences[absence.employe_id].append(absence)
    heures = defaultdict(dict)
    for ligne in heures_q.all():
        heures[ligne.employe_id][ligne.jour] = ligne.minutes
    deplacements = defaultdict(list)
    for deplacement in deplacements_q.order_by(Deplacement.date).all():
        deplacements[deplacement.employe_id].append(deplacement)

    resultat = []
    for employe in employes_q.order_by(Employe.nom, Employe.prenom).all():
        contrats = employe.contrats_sur_periode(debut, fin)
        a_des_saisies = employe.id in absences or employe.id in heures or employe.id in deplacements
        if not contrats and not a_des_saisies and employe_id is None:
            continue
        resultat.append({
            'employe': employe,
            'contrats': contrats,
            'absences': absences[employe.id],
            'heures': heures[employe.id],
            'deplacements': deplacements[employe.id],
            'total_minutes': sum(heures[employe.id].values()),
            'total_km': sum(float(d.km) for d in deplacements[employe.id]),
            'mouvements': _mouvements(employe, debut, fin),
        })
    return resultat


def serialiser_mois(debut, fin, lignes):
    fermetures = JourFermeture.query.filter(JourFermeture.date.between(debut, fin)).order_by(JourFermeture.date).all()
    employes = []
    for ligne in lignes:
        employe = ligne['employe']
        data = {
            'id': employe.id,
            'nom': employe.nom,
            'prenom': employe.prenom,
            'contrats': [c.to_dict() for c in ligne['contrats']],
            'absences': [a.to_dict() for a in ligne['absences']],
            'heures': {jour.isoformat(): valeur for jour, valeur in sorted(ligne['heures'].items())},
            'total_minutes': ligne['total_minutes'],
            'total_km': ligne['total_km'],
            'mouvements': ligne['mouvements'],
            'deplacements': [d.to_dict() for d in ligne['deplacements']],
        }
        employes.append(data)
    return {
        'mois': debut.strftime('%Y-%m'),
        'libelle': libelle_mois(debut),
        'debut': debut.isoformat(),
        'fin': fin.isoformat(),
        'jours_fermeture': [j.to_dict() for j in fermetures],
        'employes': employes,
    }


def _hors_contrat(contrats, jour):
    return not any(c.date_debut <= jour and (c.date_fin is None or c.date_fin >= jour) for c in contrats)


def controles(debut, fin, lignes):
    """Contrôles avant export. Les « bloquants » empêchent l'export (aucun à ce jour : déplacements déclaratifs)."""
    bloquants, avertissements, infos = [], [], []
    for ligne in lignes:
        employe = ligne['employe']
        nom = f'{employe.prenom} {employe.nom}'
        contrats = employe.contrats

        if not ligne['contrats']:
            avertissements.append(f'{nom} : des saisies existent ce mois-ci mais aucun contrat ne couvre le mois')

        for jour, valeur in sorted(ligne['heures'].items()):
            absence = next((a for a in ligne['absences'] if a.couvre(jour)), None)
            if absence:
                avertissements.append(
                    f'{nom} : {format_minutes(valeur)} le {format_date_fr(jour)} '
                    f'alors qu’il/elle est absent(e) ({absence.motif.libelle})'
                )
            if _hors_contrat(contrats, jour):
                avertissements.append(f'{nom} : heures +/- le {format_date_fr(jour)} en dehors de son contrat')
        for deplacement in ligne['deplacements']:
            if _hors_contrat(contrats, deplacement.date):
                avertissements.append(f'{nom} : déplacement le {format_date_fr(deplacement.date)} en dehors de son contrat')
        for absence in ligne['absences']:
            jour = max(absence.date_debut, debut)
            dernier = min(fin, absence.date_reprise - timedelta(days=1)) if absence.date_reprise else fin
            if ligne['contrats'] and all(_hors_contrat(contrats, jour + timedelta(days=n)) for n in range((dernier - jour).days + 1)):
                avertissements.append(f'{nom} : absence du {format_date_fr(absence.date_debut)} en dehors de son contrat')
            if absence.date_reprise is None:
                infos.append(f'{nom} : absence en cours ({absence.motif.libelle} depuis le {format_date_fr(absence.date_debut)})')

        if len(ligne['contrats']) > 1:
            infos.append(f'{nom} : changement de contrat dans le mois ({_texte_contrats(ligne["contrats"], debut, fin)})')

    return {'bloquants': bloquants, 'avertissements': avertissements, 'infos': infos}


ENTETES_RECAP = [
    'Nom', 'Prénom', 'Contrat (h/mois)', "Périodes d'absence", 'Km déplacements',
]


def lignes_recap(debut, fin, lignes):
    """Lignes du récapitulatif : valeurs brutes (nombres en float, None si vide)."""
    resultat = []
    for ligne in lignes:
        employe = ligne['employe']
        contrats = ligne['contrats']
        contrat = contrats[0].heures if len(contrats) == 1 else (_texte_contrats(contrats, debut, fin) if contrats else None)
        resultat.append([
            employe.nom.upper(),
            employe.prenom,
            contrat,
            ' ; '.join(texte_absence(a) for a in ligne['absences']) or None,
            ligne['total_km'] or None,
        ])
    return resultat
