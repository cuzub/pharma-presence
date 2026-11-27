"""Planning de présence : une trame semaine 1 / semaine 2 par personne et exceptions à la journée. Saisie réservée aux admins.

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


@planning_bp.route('/trame', methods=['GET'])
@admin_requis
def lire_trame():
    titulaire = _titulaire(request.args.get('employe_id', type=int), None)
    trame = TramePlanning.query.filter_by(**titulaire).first()
    return jsonify({'plages': PLAGES, 'trame': trame.to_dict() if trame else None}), 200


@planning_bp.route('/trame', methods=['PUT'])
@admin_requis
def enregistrer_trame():
    """Crée ou remplace l'unique planning (semaine 1 / semaine 2) du titulaire, valable pour toutes les dates."""
    data = donnees_json()
    titulaire = _titulaire(data.get('employe_id'), data.get('utilisateur_id'))
    horaires = valider_horaires_trame(data.get('horaires'))
    trame = TramePlanning.query.filter_by(**titulaire).first()
    if trame is None:
        trame = TramePlanning(**titulaire)
        db.session.add(trame)
    trame.horaires = horaires
    trame.updated_by_id = current_user.id
    db.session.commit()
    return jsonify(trame.to_dict()), 200


@planning_bp.route('/trame', methods=['DELETE'])
@admin_requis
def supprimer_trame():
    titulaire = _titulaire(request.args.get('employe_id', type=int), None)
    TramePlanning.query.filter_by(**titulaire).delete()
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
