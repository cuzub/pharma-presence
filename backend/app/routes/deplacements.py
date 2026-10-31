from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from flask_jwt_extended import current_user

from app.extensions import db
from app.models import Deplacement, Employe, MotifDeplacement
from app.securite import admin_requis, connexion_requise, employe_courant_id
from app.utils import ApiError, bornes_mois, donnees_json, parse_date, parse_decimal, texte

deplacements_bp = Blueprint('deplacements', __name__, url_prefix='/api/deplacements')

_STATUTS = {Deplacement.EN_ATTENTE, Deplacement.VALIDE, Deplacement.REFUSE}


def _get(deplacement_id):
    deplacement = db.session.get(Deplacement, deplacement_id)
    if deplacement is None:
        raise ApiError('Déplacement introuvable', 404)
    return deplacement


def _verifier_modifiable_par_employe(deplacement):
    """Un employé ne touche qu'à ses propres déclarations non encore validées."""
    if deplacement.employe_id != employe_courant_id():
        raise ApiError('Déplacement introuvable', 404)
    if deplacement.statut == Deplacement.VALIDE:
        raise ApiError('Ce déplacement a déjà été validé et ne peut plus être modifié', 409)


def _km(valeur, cle='km'):
    km = parse_decimal(valeur, cle)
    if km > 5000:
        raise ApiError('Distance trop élevée (5000 km maximum)')
    return km


def _remplir(deplacement, data):
    """Motif connu : libellé et km recopiés depuis le motif. « Autre » (motif_deplacement_id vide) : précision et km libres."""
    deplacement.date = parse_date(data.get('date'), 'date')
    motif_id = data.get('motif_deplacement_id')
    if motif_id in (None, ''):
        deplacement.motif_deplacement_id = None
        deplacement.motif = texte(data, 'motif')
        deplacement.km = _km(data.get('km'))
    else:
        if not isinstance(motif_id, int) or isinstance(motif_id, bool):
            raise ApiError('Motif de déplacement invalide')
        motif = db.session.get(MotifDeplacement, motif_id)
        if motif is None:
            raise ApiError('Motif de déplacement introuvable')
        # Motif inchangé : on garde le libellé et les km enregistrés à l'origine (historique figé).
        if deplacement.id is None or deplacement.motif_deplacement_id != motif.id:
            if not motif.actif:
                raise ApiError("Ce motif de déplacement n'est plus proposé")
            deplacement.motif_deplacement_id = motif.id
            deplacement.motif = motif.libelle
            deplacement.km = motif.km
    deplacement.updated_by_id = current_user.id


def _valider(deplacement):
    deplacement.statut = Deplacement.VALIDE
    deplacement.motif_refus = None
    deplacement.valide_par_id = current_user.id
    deplacement.valide_le = datetime.now(timezone.utc)


@deplacements_bp.route('', methods=['GET'])
@connexion_requise()
def lister():
    query = Deplacement.query.join(Employe)
    if current_user.est_admin:
        employe_id = request.args.get('employe_id', type=int)
        if employe_id:
            query = query.filter(Deplacement.employe_id == employe_id)
    else:
        query = query.filter(Deplacement.employe_id == employe_courant_id())

    statut = request.args.get('statut')
    if statut:
        if statut not in _STATUTS:
            raise ApiError('Statut invalide')
        query = query.filter(Deplacement.statut == statut)
    if request.args.get('mois'):
        debut, fin = bornes_mois(request.args['mois'])
        query = query.filter(Deplacement.date.between(debut, fin))
    deplacements = query.order_by(Deplacement.date.desc(), Employe.nom).all()
    return jsonify([d.to_dict() for d in deplacements]), 200


@deplacements_bp.route('', methods=['POST'])
@connexion_requise()
def creer():
    data = donnees_json()
    deplacement = Deplacement()
    if current_user.est_admin:
        employe_id = data.get('employe_id')
        if not isinstance(employe_id, int) or db.session.get(Employe, employe_id) is None:
            raise ApiError('Employé introuvable')
        deplacement.employe_id = employe_id
        _remplir(deplacement, data)
        # Saisi directement par la pharmacienne : validé d'office.
        _valider(deplacement)
    else:
        deplacement.employe_id = employe_courant_id()
        deplacement.statut = Deplacement.EN_ATTENTE
        _remplir(deplacement, data)
    db.session.add(deplacement)
    db.session.commit()
    return jsonify(deplacement.to_dict()), 201


@deplacements_bp.route('/<int:deplacement_id>', methods=['PUT'])
@connexion_requise()
def modifier(deplacement_id):
    deplacement = _get(deplacement_id)
    if not current_user.est_admin:
        _verifier_modifiable_par_employe(deplacement)
        deplacement.statut = Deplacement.EN_ATTENTE
        deplacement.motif_refus = None
    _remplir(deplacement, donnees_json())
    db.session.commit()
    return jsonify(deplacement.to_dict()), 200


@deplacements_bp.route('/<int:deplacement_id>', methods=['DELETE'])
@connexion_requise()
def supprimer(deplacement_id):
    deplacement = _get(deplacement_id)
    if not current_user.est_admin:
        _verifier_modifiable_par_employe(deplacement)
    db.session.delete(deplacement)
    db.session.commit()
    return '', 204


@deplacements_bp.route('/<int:deplacement_id>/valider', methods=['POST'])
@admin_requis
def valider(deplacement_id):
    deplacement = _get(deplacement_id)
    _valider(deplacement)
    deplacement.updated_by_id = current_user.id
    db.session.commit()
    return jsonify(deplacement.to_dict()), 200


@deplacements_bp.route('/<int:deplacement_id>/refuser', methods=['POST'])
@admin_requis
def refuser(deplacement_id):
    deplacement = _get(deplacement_id)
    deplacement.statut = Deplacement.REFUSE
    deplacement.motif_refus = texte(donnees_json(), 'motif_refus')
    deplacement.valide_par_id = current_user.id
    deplacement.valide_le = datetime.now(timezone.utc)
    deplacement.updated_by_id = current_user.id
    db.session.commit()
    return jsonify(deplacement.to_dict()), 200


# --- Motifs de déplacement ---------------------------------------------------

def _remplir_motif(motif, data):
    libelle = texte(data, 'libelle', longueur_max=80)
    doublon = MotifDeplacement.query.filter(db.func.lower(MotifDeplacement.libelle) == libelle.lower()).first()
    if doublon is not None and doublon.id != motif.id:
        raise ApiError('Ce motif de déplacement existe déjà', 409)
    if libelle.lower() == 'autre':
        raise ApiError('« Autre » est toujours proposé, inutile de le créer', 409)
    motif.libelle = libelle
    motif.km = _km(data.get('km'))
    motif.actif = bool(data.get('actif', True))
    if isinstance(data.get('ordre'), int):
        motif.ordre = data['ordre']
    motif.updated_by_id = current_user.id


@deplacements_bp.route('/motifs', methods=['GET'])
@connexion_requise()
def lister_motifs():
    motifs = MotifDeplacement.query.order_by(MotifDeplacement.ordre, MotifDeplacement.libelle).all()
    return jsonify([m.to_dict() for m in motifs]), 200


@deplacements_bp.route('/motifs', methods=['POST'])
@admin_requis
def creer_motif():
    motif = MotifDeplacement(ordre=(db.session.query(db.func.max(MotifDeplacement.ordre)).scalar() or 0) + 1)
    _remplir_motif(motif, donnees_json())
    db.session.add(motif)
    db.session.commit()
    return jsonify(motif.to_dict()), 201


@deplacements_bp.route('/motifs/<int:motif_id>', methods=['PUT'])
@admin_requis
def modifier_motif(motif_id):
    motif = db.session.get(MotifDeplacement, motif_id)
    if motif is None:
        raise ApiError('Motif de déplacement introuvable', 404)
    _remplir_motif(motif, donnees_json())
    db.session.commit()
    return jsonify(motif.to_dict()), 200
