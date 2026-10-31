"""Statistiques annuelles des heures en plus / en moins, par employé et par mois."""

from datetime import date

from sqlalchemy import case, extract, func, or_

from app.extensions import db
from app.models import Contrat, Employe, HeuresEnPlus, RegularisationHeures

MOIS = range(12)


def _vide():
    return [0] * 12


def statistiques_annee(annee):
    debut, fin = date(annee, 1, 1), date(annee, 12, 31)

    # Heures du jour et régularisations (crédits / débits) comptent toutes deux.
    par_employe = {}
    for modele in (HeuresEnPlus, RegularisationHeures):
        mois = extract('month', modele.jour)
        plus = func.sum(case((modele.minutes > 0, modele.minutes), else_=0))
        moins = func.sum(case((modele.minutes < 0, modele.minutes), else_=0))
        lignes = (
            db.session.query(modele.employe_id, mois, plus, moins)
            .filter(modele.jour >= debut, modele.jour <= fin)
            .group_by(modele.employe_id, mois)
            .all()
        )
        for employe_id, numero, total_plus, total_moins in lignes:
            donnees = par_employe.setdefault(employe_id, {'plus': _vide(), 'moins': _vide()})
            donnees['plus'][int(numero) - 1] += int(total_plus or 0)
            donnees['moins'][int(numero) - 1] += int(total_moins or 0)

    ids_contrats = [
        employe_id
        for (employe_id,) in db.session.query(Contrat.employe_id)
        .filter(Contrat.date_debut <= fin, or_(Contrat.date_fin.is_(None), Contrat.date_fin >= debut))
        .distinct()
        .all()
    ]
    ids = set(par_employe) | set(ids_contrats)
    employes = (
        Employe.query.filter(Employe.id.in_(ids)).order_by(Employe.nom, Employe.prenom).all() if ids else []
    )

    resultats = []
    totaux = {'plus': _vide(), 'moins': _vide()}
    for employe in employes:
        donnees = par_employe.get(employe.id, {'plus': _vide(), 'moins': _vide()})
        plus_mois, moins_mois = donnees['plus'], donnees['moins']
        net = [plus_mois[m] + moins_mois[m] for m in MOIS]
        for m in MOIS:
            totaux['plus'][m] += plus_mois[m]
            totaux['moins'][m] += moins_mois[m]
        resultats.append({
            'id': employe.id,
            'nom': employe.nom,
            'prenom': employe.prenom,
            'actif': bool(employe.utilisateur and employe.utilisateur.actif),
            'plus': plus_mois,
            'moins': moins_mois,
            'net': net,
            'total_plus': sum(plus_mois),
            'total_moins': sum(moins_mois),
            'total_net': sum(net),
        })

    net_equipe = [totaux['plus'][m] + totaux['moins'][m] for m in MOIS]
    return {
        'annee': annee,
        'employes': resultats,
        'totaux': {
            'plus': totaux['plus'],
            'moins': totaux['moins'],
            'net': net_equipe,
            'total_plus': sum(totaux['plus']),
            'total_moins': sum(totaux['moins']),
            'total_net': sum(net_equipe),
        },
    }
