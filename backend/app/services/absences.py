"""Blocage de la saisie pendant les absences (heures et déplacements)."""

from sqlalchemy import or_

from app.extensions import db
from app.models import Absence, Deplacement, HeuresEnPlus
from app.services.journal import instantane_deplacement, instantane_heures, journaliser
from app.services.mois import format_minutes, format_nombre_fr
from app.utils import ApiError, format_date_fr


def absence_bloquante(employe_id, jour):
    """L'absence d'un motif bloquant qui couvre ce jour, sinon None."""
    return (
        Absence.query.filter(
            Absence.employe_id == employe_id,
            Absence.date_debut <= jour,
            or_(Absence.date_reprise.is_(None), Absence.date_reprise > jour),
            Absence.motif.has(bloque_saisie=True),
        )
        .first()
    )


def verifier_jour_saisissable(employe, jour):
    absence = absence_bloquante(employe.id, jour)
    if absence is not None:
        raise ApiError(
            f'{employe.prenom} est absente le {format_date_fr(jour)} ({absence.motif.libelle}) : saisie impossible',
            409,
            'jour_absent',
        )


def _decrire(saisie):
    if isinstance(saisie, HeuresEnPlus):
        return {'type': 'heures', 'id': saisie.id, 'jour': saisie.jour.isoformat(), 'libelle': format_minutes(saisie.minutes)}
    return {
        'type': 'deplacement',
        'id': saisie.id,
        'jour': saisie.date.isoformat(),
        'libelle': f'{saisie.motif} {format_nombre_fr(float(saisie.km))} km',
    }


def saisies_en_conflit(employe_id, debut, reprise=None):
    """Heures et déplacements de l'employé dans la période [debut, reprise[ (sans reprise : à partir de debut)."""
    heures = HeuresEnPlus.query.filter(HeuresEnPlus.employe_id == employe_id, HeuresEnPlus.jour >= debut)
    deplacements = Deplacement.query.filter(Deplacement.employe_id == employe_id, Deplacement.date >= debut)
    if reprise:
        heures = heures.filter(HeuresEnPlus.jour < reprise)
        deplacements = deplacements.filter(Deplacement.date < reprise)
    saisies = [*heures.all(), *deplacements.all()]
    return sorted(saisies, key=lambda s: s.jour if isinstance(s, HeuresEnPlus) else s.date)


def supprimer_saisies(saisies, employe_id):
    """Supprime les saisies en conflit, avec trace dans le journal (dans la transaction en cours)."""
    for saisie in saisies:
        if isinstance(saisie, HeuresEnPlus):
            journaliser('heures', 'suppression', employe_id, saisie.id, avant=instantane_heures(saisie))
        else:
            journaliser('deplacement', 'suppression', employe_id, saisie.id, avant=instantane_deplacement(saisie))
        db.session.delete(saisie)


def decrire_saisies(saisies):
    return [_decrire(s) for s in saisies]
