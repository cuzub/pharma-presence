import re

from flask import Blueprint, jsonify

from app.extensions import db
from app.models import ParametresMail
from app.securite import admin_requis
from app.utils import ApiError, donnees_json, texte

parametres_bp = Blueprint('parametres', __name__, url_prefix='/api/parametres')

_EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


def _courant():
    parametres = db.session.get(ParametresMail, 1)
    return parametres or ParametresMail(id=1, destinataire='', titre='', texte='')


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
