import re

from flask import Blueprint, jsonify
from flask_jwt_extended import current_user

from app.extensions import db
from app.models import ParametresIK, ParametresMail
from app.securite import admin_requis
from app.utils import ApiError, donnees_json, parse_decimal, texte

parametres_bp = Blueprint('parametres', __name__, url_prefix='/api/parametres')

_EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


def _courant():
    parametres = db.session.get(ParametresMail, 1)
    return parametres or ParametresMail(id=1, destinataire='', titre='', texte='')


def _ik_courant():
    parametres = db.session.get(ParametresIK, 1)
    return parametres.to_dict() if parametres else {'coefficient': None}


def _reponse_ik():
    return {**_ik_courant(), 'nom_affiche': current_user.nom_affiche or ''}


@parametres_bp.route('/mail', methods=['GET'])
@admin_requis
def lire_mail():
    return jsonify(_courant().to_dict()), 200


@parametres_bp.route('/mail', methods=['PUT'])
@admin_requis
def modifier_mail():
    data = donnees_json()
    destinataire = texte(data, 'destinataire', obligatoire=False, longueur_max=254) or ''
    if destinataire and not _EMAIL_RE.match(destinataire):
        raise ApiError('Adresse e-mail du destinataire invalide')
    titre = texte(data, 'titre', obligatoire=False, longueur_max=200) or ''
    corps = texte(data, 'texte', obligatoire=False, longueur_max=5000) or ''

    parametres = db.session.get(ParametresMail, 1)
    if parametres is None:
        parametres = ParametresMail(id=1)
        db.session.add(parametres)
    parametres.destinataire = destinataire
    parametres.titre = titre
    parametres.texte = corps
    db.session.commit()
    return jsonify(parametres.to_dict()), 200


@parametres_bp.route('/ik', methods=['GET'])
@admin_requis
def lire_ik():
    return jsonify(_reponse_ik()), 200


@parametres_bp.route('/ik', methods=['PUT'])
@admin_requis
def modifier_ik():
    data = donnees_json()
    coefficient = parse_decimal(data.get('coefficient'), 'coefficient')
    if coefficient > 10:
        raise ApiError('Coefficient IK trop élevé (10 €/km maximum)')
    if coefficient.as_tuple().exponent < -3:
        raise ApiError('Coefficient IK : 3 décimales maximum')
    current_user.nom_affiche = texte(data, 'nom_affiche', obligatoire=False, longueur_max=100)

    parametres = db.session.get(ParametresIK, 1)
    if parametres is None:
        parametres = ParametresIK(id=1)
        db.session.add(parametres)
    parametres.coefficient = coefficient
    parametres.updated_by_id = current_user.id
    db.session.commit()
    return jsonify(_reponse_ik()), 200
