"""Solde cumulé des heures +/- : heures du jour et régularisations, sur tout l'historique."""

from collections import defaultdict

from app.extensions import db
from app.models import HeuresEnPlus, RegularisationHeures


def soldes_jusqua(fin, employe_ids=None):
    """Minutes cumulées par employé pour tous les jours jusqu'à `fin` inclus."""
    soldes = defaultdict(int)
    for modele in (HeuresEnPlus, RegularisationHeures):
        query = db.session.query(modele.employe_id, db.func.sum(modele.minutes)).filter(modele.jour <= fin)
        if employe_ids is not None:
            query = query.filter(modele.employe_id.in_(employe_ids))
        for employe_id, total in query.group_by(modele.employe_id).all():
            soldes[employe_id] += int(total or 0)
    return soldes
