"""Planning de présence : trames semaine 1 / semaine 2 et exceptions à la journée. Saisie réservée aux admins.

Un admin gère le planning de tous les employés et le sien (pas celui d'un autre admin).
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import current_user

from app.extensions import db
from app.models import Employe, ExceptionPlanning, TramePlanning
from app.securite import admin_requis
from app.services.planning import PLAGES, valider_horaires_trame, valider_jour
from app.utils import ApiError, donnees_json, parse_date

planning_bp = Blueprint('planning', __name__, url_prefix='/api/planning')


def _titulaire(employe_id, utilisateur_id):
    """{'employe_id': …} ou {'utilisateur_id': current_user.id}."""
    if employe_id not in (None, ''):
        if not isinstance(employe_id, int) or isinstance(employe_id, bool) or db.session.get(Employe, employe_id) is None:
            raise ApiError('Employé introuvable', 404)
        return {'employe_id': employe_id, 'utilisateur_id': None}
    if utilisateur_id not in (None, '') and utilisateur_id != current_user.id:
        raise ApiError('Vous ne pouvez modifier que votre propre planning', 403, 'acces_refuse')
    return {'employe_id': None, 'utilisateur_id': current_user.id}


def _verifier_proprietaire(objet):
    if objet.utilisateur_id is not None and objet.utilisateur_id != current_user.id:
        raise ApiError('Vous ne pouvez modifier que votre propre planning', 403, 'acces_refuse')


def _trame(trame_id):
    trame = db.session.get(TramePlanning, trame_id)
    if trame is None:
        raise ApiError('Planning introuvable', 404)
    _verifier_proprietaire(trame)
    return trame


def _date_debut_libre(titulaire, date_debut, sauf_id=None):
    requete = TramePlanning.query.filter_by(date_debut=date_debut, **titulaire)
    if sauf_id is not None:
        requete = requete.filter(TramePlanning.id != sauf_id)
    if requete.first():
        raise ApiError('Un planning commence déjà à cette date', 409)


@planning_bp.route('/trames', methods=['GET'])
@admin_requis
def lister_trames():
    employe_id = request.args.get('employe_id', type=int)
    titulaire = _titulaire(employe_id, None)
    trames = TramePlanning.query.filter_by(**titulaire).order_by(TramePlanning.date_debut.desc()).all()
    return jsonify({'plages': PLAGES, 'trames': [t.to_dict() for t in trames]}), 200


@planning_bp.route('/trames', methods=['POST'])
@admin_requis
def creer_trame():
    data = donnees_json()
    titulaire = _titulaire(data.get('employe_id'), data.get('utilisateur_id'))
    date_debut = parse_date(data.get('date_debut'), 'date_debut')
    _date_debut_libre(titulaire, date_debut)
    trame = TramePlanning(
        **titulaire, date_debut=date_debut, horaires=valider_horaires_trame(data.get('horaires')),
        updated_by_id=current_user.id,
    )
    db.session.add(trame)
    db.session.commit()
    return jsonify(trame.to_dict()), 201


@planning_bp.route('/trames/<int:trame_id>', methods=['PUT'])
@admin_requis
def modifier_trame(trame_id):
    trame = _trame(trame_id)
    data = donnees_json()
    date_debut = parse_date(data.get('date_debut'), 'date_debut')
    _date_debut_libre({'employe_id': trame.employe_id, 'utilisateur_id': trame.utilisateur_id}, date_debut, trame.id)
    trame.date_debut = date_debut
    trame.horaires = valider_horaires_trame(data.get('horaires'))
    trame.updated_by_id = current_user.id
    db.session.commit()
    return jsonify(trame.to_dict()), 200


@planning_bp.route('/trames/<int:trame_id>', methods=['DELETE'])
@admin_requis
def supprimer_trame(trame_id):
    db.session.delete(_trame(trame_id))
    db.session.commit()
    return '', 204


@planning_bp.route('/exceptions', methods=['PUT'])
@admin_requis
def enregistrer_exception():
    """Crée ou remplace les horaires d'un jour. Matin et après-midi vides = pas présent ce jour-là."""
    data = donnees_json()
    titulaire = _titulaire(data.get('employe_id'), data.get('utilisateur_id'))
    jour = parse_date(data.get('jour'), 'jour')
    horaires = valider_jour({'matin': data.get('matin'), 'apres_midi': data.get('apres_midi')}, jour.weekday(), 'Horaires du jour')
    exception = ExceptionPlanning.query.filter_by(jour=jour, **titulaire).first()
    if exception is None:
        exception = ExceptionPlanning(**titulaire, jour=jour)
        db.session.add(exception)
    exception.horaires = horaires
    exception.updated_by_id = current_user.id
    db.session.commit()
    return jsonify(exception.to_dict()), 200


@planning_bp.route('/exceptions', methods=['DELETE'])
@admin_requis
def supprimer_exception():
    """Revient au planning habituel pour ce jour."""
    titulaire = _titulaire(request.args.get('employe_id', type=int), request.args.get('utilisateur_id', type=int))
    jour = parse_date(request.args.get('jour'), 'jour')
    ExceptionPlanning.query.filter_by(jour=jour, **titulaire).delete()
    db.session.commit()
    return '', 204
