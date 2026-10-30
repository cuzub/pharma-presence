from flask import Blueprint, jsonify, request
from flask_jwt_extended import current_user
from sqlalchemy import or_

from app.extensions import db
from app.models import Absence, Employe, MotifAbsence
from app.securite import admin_requis, connexion_requise, employe_courant_id
from app.utils import ApiError, donnees_json, parse_date, texte

absences_bp = Blueprint('absences', __name__, url_prefix='/api/absences')


def _valider(data, absence):
    employe_id = data.get('employe_id')
    if not isinstance(employe_id, int) or db.session.get(Employe, employe_id) is None:
        raise ApiError('Employé introuvable')
    motif = db.session.get(MotifAbsence, data.get('motif_id')) if isinstance(data.get('motif_id'), int) else None
    if motif is None:
        raise ApiError("Motif d'absence introuvable")
    if not motif.actif and motif.id != absence.motif_id:
        raise ApiError("Ce motif d'absence n'est plus utilisé")
    date_debut = parse_date(data.get('date_debut'), 'date_debut')
    date_reprise = parse_date(data.get('date_reprise'), 'date_reprise', obligatoire=False)
    if date_reprise and date_reprise <= date_debut:
        raise ApiError('Le jour de reprise doit être après le premier jour d’absence')

    chevauchement = Absence.query.filter(
        Absence.employe_id == employe_id,
        Absence.id != (absence.id or 0),
        or_(Absence.date_reprise.is_(None), Absence.date_reprise > date_debut),
    )
    if date_reprise:
        chevauchement = chevauchement.filter(Absence.date_debut < date_reprise)
    autre = chevauchement.first()
    if autre:
        reprise = autre.date_reprise.strftime('%d/%m/%Y') if autre.date_reprise else 'en cours'
        raise ApiError(
            f'Chevauche une autre absence ({autre.motif.libelle} du '
            f'{autre.date_debut.strftime("%d/%m/%Y")}, reprise {reprise})',
            409,
        )

    absence.employe_id = employe_id
    absence.motif = motif
    absence.date_debut = date_debut
    absence.date_reprise = date_reprise
    absence.commentaire = texte(data, 'commentaire', obligatoire=False)
    absence.updated_by_id = current_user.id


@absences_bp.route('', methods=['GET'])
@connexion_requise()
def lister():
    query = Absence.query.join(Employe)
    if current_user.est_admin:
        employe_id = request.args.get('employe_id', type=int)
        if employe_id:
            query = query.filter(Absence.employe_id == employe_id)
    else:
        query = query.filter(Absence.employe_id == employe_courant_id())

    debut = parse_date(request.args.get('debut'), 'debut', obligatoire=False)
    fin = parse_date(request.args.get('fin'), 'fin', obligatoire=False)
    if debut:
        query = query.filter(or_(Absence.date_reprise.is_(None), Absence.date_reprise > debut))
    if fin:
        query = query.filter(Absence.date_debut <= fin)
    absences = query.order_by(Absence.date_debut.desc(), Employe.nom).all()
    return jsonify([a.to_dict() for a in absences]), 200


@absences_bp.route('', methods=['POST'])
@admin_requis
def creer():
    absence = Absence()
    _valider(donnees_json(), absence)
    db.session.add(absence)
    db.session.commit()
    return jsonify(absence.to_dict()), 201


@absences_bp.route('/<int:absence_id>', methods=['PUT'])
@admin_requis
def modifier(absence_id):
    absence = db.session.get(Absence, absence_id)
    if absence is None:
        raise ApiError('Absence introuvable', 404)
    _valider(donnees_json(), absence)
    db.session.commit()
    return jsonify(absence.to_dict()), 200


@absences_bp.route('/<int:absence_id>', methods=['DELETE'])
@admin_requis
def supprimer(absence_id):
    absence = db.session.get(Absence, absence_id)
    if absence is None:
        raise ApiError('Absence introuvable', 404)
    db.session.delete(absence)
    db.session.commit()
    return '', 204
