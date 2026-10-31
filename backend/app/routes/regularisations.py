"""Régularisations d'heures +/- : crédits et débits saisis par la pharmacienne depuis la fiche employé."""

from flask import Blueprint, jsonify
from flask_jwt_extended import current_user

from app.extensions import db
from app.models import Employe, RegularisationHeures
from app.securite import admin_requis
from app.services import fenetre
from app.services.journal import instantane_regularisation, journaliser
from app.services.solde import soldes_jusqua
from app.utils import ApiError, donnees_json, parse_date, texte

regularisations_bp = Blueprint('regularisations', __name__, url_prefix='/api')

_MESSAGE_MINUTES = 'Durée invalide : nombre de minutes non nul, par tranche de 5'


def _employe(employe_id):
    employe = db.session.get(Employe, employe_id)
    if employe is None:
        raise ApiError('Employé introuvable', 404)
    return employe


def _regularisation(regularisation_id):
    regularisation = db.session.get(RegularisationHeures, regularisation_id)
    if regularisation is None:
        raise ApiError('Régularisation introuvable', 404)
    return regularisation


def _minutes(valeur):
    if isinstance(valeur, str):
        try:
            valeur = int(valeur.strip())
        except ValueError:
            raise ApiError(_MESSAGE_MINUTES) from None
    if isinstance(valeur, bool) or not isinstance(valeur, int) or valeur == 0:
        raise ApiError(_MESSAGE_MINUTES)
    if valeur % 5:
        raise ApiError('Les minutes se saisissent par tranche de 5')
    if abs(valeur) > RegularisationHeures.MINUTES_MAX:
        raise ApiError('500 heures maximum par régularisation')
    return valeur


def _remplir(regularisation, data):
    regularisation.jour = parse_date(data.get('jour'), 'jour')
    regularisation.minutes = _minutes(data.get('minutes'))
    regularisation.commentaire = texte(data, 'commentaire', obligatoire=False, longueur_max=200)
    regularisation.updated_by_id = current_user.id


@regularisations_bp.route('/employes/<int:employe_id>/regularisations', methods=['GET'])
@admin_requis
def lister(employe_id):
    _employe(employe_id)
    regularisations = (
        RegularisationHeures.query.filter_by(employe_id=employe_id)
        .order_by(RegularisationHeures.jour.desc(), RegularisationHeures.id.desc())
        .all()
    )
    return jsonify({
        'solde_minutes': soldes_jusqua(fenetre.aujourdhui(), [employe_id])[employe_id],
        'regularisations': [r.to_dict() for r in regularisations],
    }), 200


@regularisations_bp.route('/employes/<int:employe_id>/regularisations', methods=['POST'])
@admin_requis
def creer(employe_id):
    _employe(employe_id)
    regularisation = RegularisationHeures(employe_id=employe_id)
    _remplir(regularisation, donnees_json())
    db.session.add(regularisation)
    db.session.flush()
    journaliser('regularisation', 'creation', employe_id, regularisation.id, apres=instantane_regularisation(regularisation))
    db.session.commit()
    return jsonify(regularisation.to_dict()), 201


@regularisations_bp.route('/regularisations/<int:regularisation_id>', methods=['PUT'])
@admin_requis
def modifier(regularisation_id):
    regularisation = _regularisation(regularisation_id)
    avant = instantane_regularisation(regularisation)
    _remplir(regularisation, donnees_json())
    journaliser(
        'regularisation', 'modification', regularisation.employe_id, regularisation.id,
        avant, instantane_regularisation(regularisation),
    )
    db.session.commit()
    return jsonify(regularisation.to_dict()), 200


@regularisations_bp.route('/regularisations/<int:regularisation_id>', methods=['DELETE'])
@admin_requis
def supprimer(regularisation_id):
    regularisation = _regularisation(regularisation_id)
    journaliser(
        'regularisation', 'suppression', regularisation.employe_id, regularisation.id,
        avant=instantane_regularisation(regularisation),
    )
    db.session.delete(regularisation)
    db.session.commit()
    return '', 204
