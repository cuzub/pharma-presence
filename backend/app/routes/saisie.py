import re

from flask import Blueprint, jsonify
from flask_jwt_extended import current_user

from app.extensions import db
from app.models import Employe, HeuresEnPlus, JourFermeture, MotifAbsence
from app.securite import admin_requis, connexion_requise
from app.utils import ApiError, donnees_json, parse_date, parse_decimal, texte

saisie_bp = Blueprint('saisie', __name__, url_prefix='/api')

_COULEUR_RE = re.compile(r'^#[0-9a-fA-F]{6}$')


# --- Heures en plus -------------------------------------------------------

@saisie_bp.route('/heures', methods=['PUT'])
@admin_requis
def enregistrer_heures():
    """Enregistre le nombre d'heures en plus d'un employé pour un jour (0 ou vide = suppression)."""
    data = donnees_json()
    employe_id = data.get('employe_id')
    if not isinstance(employe_id, int) or db.session.get(Employe, employe_id) is None:
        raise ApiError('Employé introuvable')
    jour = parse_date(data.get('jour'), 'jour')
    existant = HeuresEnPlus.query.filter_by(employe_id=employe_id, jour=jour).first()

    valeur = data.get('heures')
    if valeur in (None, '', 0, '0'):
        if existant:
            db.session.delete(existant)
            db.session.commit()
        return jsonify({'employe_id': employe_id, 'jour': jour.isoformat(), 'heures': 0}), 200

    heures = parse_decimal(valeur, 'heures')
    if heures > 24:
        raise ApiError('24 heures maximum par jour')
    if (heures * 4) % 1 != 0:
        raise ApiError('Les heures se saisissent au quart d’heure près (ex : 1,25 / 1,5 / 1,75)')

    if existant is None:
        existant = HeuresEnPlus(employe_id=employe_id, jour=jour)
        db.session.add(existant)
    existant.heures = heures
    existant.updated_by_id = current_user.id
    db.session.commit()
    return jsonify(existant.to_dict()), 200


# --- Motifs d'absence ------------------------------------------------------

@saisie_bp.route('/motifs', methods=['GET'])
@connexion_requise()
def lister_motifs():
    motifs = MotifAbsence.query.order_by(MotifAbsence.ordre, MotifAbsence.libelle).all()
    return jsonify([m.to_dict() for m in motifs]), 200


def _remplir_motif(motif, data):
    motif.libelle = texte(data, 'libelle', longueur_max=80)
    couleur = (data.get('couleur') or '#6c757d').strip()
    if not _COULEUR_RE.match(couleur):
        raise ApiError('Couleur invalide (format #RRGGBB)')
    motif.couleur = couleur
    motif.actif = bool(data.get('actif', True))
    if isinstance(data.get('ordre'), int):
        motif.ordre = data['ordre']
    motif.updated_by_id = current_user.id


@saisie_bp.route('/motifs', methods=['POST'])
@admin_requis
def creer_motif():
    data = donnees_json()
    code = (texte(data, 'code', longueur_max=20) or '').upper()
    if MotifAbsence.query.filter_by(code=code).first():
        raise ApiError('Ce code de motif existe déjà', 409)
    motif = MotifAbsence(code=code, ordre=(db.session.query(db.func.max(MotifAbsence.ordre)).scalar() or 0) + 1)
    _remplir_motif(motif, data)
    db.session.add(motif)
    db.session.commit()
    return jsonify(motif.to_dict()), 201


@saisie_bp.route('/motifs/<int:motif_id>', methods=['PUT'])
@admin_requis
def modifier_motif(motif_id):
    motif = db.session.get(MotifAbsence, motif_id)
    if motif is None:
        raise ApiError('Motif introuvable', 404)
    _remplir_motif(motif, donnees_json())
    db.session.commit()
    return jsonify(motif.to_dict()), 200


# --- Jours de fermeture de la pharmacie ------------------------------------

@saisie_bp.route('/jours-fermeture', methods=['GET'])
@connexion_requise()
def lister_jours_fermeture():
    jours = JourFermeture.query.order_by(JourFermeture.date).all()
    return jsonify([j.to_dict() for j in jours]), 200


@saisie_bp.route('/jours-fermeture', methods=['POST'])
@admin_requis
def creer_jour_fermeture():
    data = donnees_json()
    jour = parse_date(data.get('date'), 'date')
    if JourFermeture.query.filter_by(date=jour).first():
        raise ApiError('Ce jour est déjà un jour de fermeture', 409)
    fermeture = JourFermeture(date=jour, libelle=texte(data, 'libelle', obligatoire=False, longueur_max=120))
    fermeture.updated_by_id = current_user.id
    db.session.add(fermeture)
    db.session.commit()
    return jsonify(fermeture.to_dict()), 201


@saisie_bp.route('/jours-fermeture/<int:jour_id>', methods=['DELETE'])
@admin_requis
def supprimer_jour_fermeture(jour_id):
    fermeture = db.session.get(JourFermeture, jour_id)
    if fermeture is None:
        raise ApiError('Jour de fermeture introuvable', 404)
    db.session.delete(fermeture)
    db.session.commit()
    return '', 204

