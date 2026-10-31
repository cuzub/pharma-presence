"""Journal des modifications : qui a créé / modifié / supprimé un déplacement, des heures ou une absence."""

from flask_jwt_extended import current_user

from app.extensions import db
from app.models import JournalModification


def instantane_deplacement(deplacement):
    return {'date': deplacement.date.isoformat(), 'motif': deplacement.motif, 'km': float(deplacement.km)}


def instantane_heures(heures):
    return {'jour': heures.jour.isoformat(), 'minutes': heures.minutes}


def instantane_absence(absence):
    return {
        'motif': absence.motif.libelle if absence.motif else None,
        'date_debut': absence.date_debut.isoformat(),
        'date_reprise': absence.date_reprise.isoformat() if absence.date_reprise else None,
        'commentaire': absence.commentaire,
    }


def journaliser(type_, action, employe_id, objet_id, avant=None, apres=None):
    """Ajoute une ligne au journal dans la transaction en cours (validée avec la modification elle-même)."""
    if action == 'modification' and avant == apres:
        return
    db.session.add(JournalModification(
        auteur_id=current_user.id,
        auteur_identifiant=current_user.identifiant,
        auteur_role=current_user.role,
        employe_id=employe_id,
        type=type_,
        action=action,
        objet_id=objet_id,
        avant=avant,
        apres=apres,
    ))
