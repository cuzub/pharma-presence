import re

from flask import Blueprint, jsonify
from flask_jwt_extended import current_user

from app.extensions import db
from app.models import Employe, HeuresEnPlus, JourFermeture, MotifAbsence
from app.securite import admin_requis, connexion_requise, employe_courant_id
from app.services.absences import verifier_jour_saisissable
from app.services.fenetre import verifier_fenetre_employe, verifier_jour_ouvert_employe
from app.services.journal import instantane_heures, journaliser
from app.utils import ApiError, donnees_json, parse_date, texte

saisie_bp = Blueprint('saisie', __name__, url_prefix='/api')

_COULEUR_RE = re.compile(r'^#[0-9a-fA-F]{6}$')


# --- Heures en plus -------------------------------------------------------

@saisie_bp.route('/heures', methods=['PUT'])
@connexion_requise()
def enregistrer_heures():
    """Minutes en plus (> 0) ou en moins (< 0) d'un employé pour un jour (0 ou vide = suppression).

    L'employé ne saisit que ses propres heures, dans la même fenêtre que ses déplacements.
    """
    data = donnees_json()
    employe_id = data.get('employe_id')
    employe = db.session.get(Employe, employe_id)
    if not isinstance(employe_id, int) or employe is None:
        raise ApiError('Employé introuvable')
    if not current_user.est_admin and employe_id != employe_courant_id():
        raise ApiError('Employé introuvable', 404)
    jour = parse_date(data.get('jour'), 'jour')
    if not current_user.est_admin:
        verifier_fenetre_employe(jour, 'Les heures +/- ne peuvent être saisies ou corrigées')
        verifier_jour_ouvert_employe(jour)
    existant = HeuresEnPlus.query.filter_by(employe_id=employe_id, jour=jour).first()
    avant = instantane_heures(existant) if existant else None

    valeur = data.get('minutes')
    if valeur in (None, ''):
        valeur = 0
    if isinstance(valeur, str):
        try:
            valeur = int(valeur.strip())
        except ValueError:
            raise ApiError('Nombre de minutes invalide (ex : 15, -30, 90)') from None
    if isinstance(valeur, bool) or not isinstance(valeur, int):
        raise ApiError('Nombre de minutes invalide (ex : 15, -30, 90)')

    if valeur != 0:
        verifier_jour_saisissable(employe, jour)
    if valeur == 0:
        if existant:
            journaliser('heures', 'suppression', employe_id, existant.id, avant=avant)
            db.session.delete(existant)
            db.session.commit()
        return jsonify({'employe_id': employe_id, 'jour': jour.isoformat(), 'minutes': 0}), 200

    if abs(valeur) > 720:
        raise ApiError('12 heures maximum (720 minutes) en plus ou en moins par jour')
    if valeur % 5:
        raise ApiError('Les minutes se saisissent par tranche de 5 (ex : 15, -30, 95)')

    if existant is None:
        existant = HeuresEnPlus(employe_id=employe_id, jour=jour)
        db.session.add(existant)
    existant.minutes = valeur
    existant.updated_by_id = current_user.id
    db.session.flush()
    journaliser('heures', 'modification' if avant else 'creation', employe_id, existant.id, avant, instantane_heures(existant))
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
    if 'bloque_saisie' in data:
        motif.bloque_saisie = bool(data['bloque_saisie'])
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

