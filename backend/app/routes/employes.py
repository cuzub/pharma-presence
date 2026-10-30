import re
from datetime import date, timedelta

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import current_user

from app.extensions import db
from app.models import Contrat, Employe, Utilisateur
from app.securite import admin_requis, verifier_mot_de_passe_valide
from app.utils import ApiError, donnees_json, parse_date, parse_decimal, texte

employes_bp = Blueprint('employes', __name__, url_prefix='/api/employes')

_IDENTIFIANT_RE = re.compile(r'^[a-z0-9][a-z0-9._-]{2,39}$')


def _identifiant(data):
    identifiant = (data.get('identifiant') or '').strip().lower()
    if not _IDENTIFIANT_RE.match(identifiant):
        raise ApiError('Identifiant invalide : 3 à 40 caractères (lettres minuscules, chiffres, point, tiret)')
    return identifiant


def _mot_de_passe_provisoire(data):
    mot_de_passe = data.get('mot_de_passe_provisoire') or ''
    verifier_mot_de_passe_valide(mot_de_passe, current_app.config['MOT_DE_PASSE_LONGUEUR_MIN'])
    return mot_de_passe


def _get_employe(employe_id):
    employe = db.session.get(Employe, employe_id)
    if employe is None:
        raise ApiError('Employé introuvable', 404)
    return employe


def _tracer(*objets):
    for objet in objets:
        objet.updated_by_id = current_user.id


def _est_en_poste(employe, aujourdhui):
    return any(c.date_fin is None or c.date_fin >= aujourdhui for c in employe.contrats)


@employes_bp.route('', methods=['GET'])
@admin_requis
def lister():
    statut = request.args.get('statut', 'actifs')
    aujourdhui = date.today()
    employes = Employe.query.order_by(Employe.nom, Employe.prenom).all()
    if statut == 'actifs':
        employes = [e for e in employes if _est_en_poste(e, aujourdhui)]
    elif statut == 'partis':
        employes = [e for e in employes if not _est_en_poste(e, aujourdhui)]
    return jsonify([e.to_dict() for e in employes]), 200


@employes_bp.route('', methods=['POST'])
@admin_requis
def creer():
    data = donnees_json()
    nom = texte(data, 'nom', longueur_max=100)
    prenom = texte(data, 'prenom', longueur_max=100)
    identifiant = _identifiant(data)
    date_entree = parse_date(data.get('date_entree'), 'date_entree')
    heures = parse_decimal(data.get('heures_mensuelles'), 'heures_mensuelles')
    mot_de_passe = _mot_de_passe_provisoire(data)

    if Utilisateur.query.filter_by(identifiant=identifiant).first():
        raise ApiError('Cet identifiant est déjà utilisé', 409)

    utilisateur = Utilisateur(identifiant=identifiant, role=Utilisateur.ROLE_EMPLOYE, actif=True)
    utilisateur.definir_mot_de_passe(mot_de_passe, provisoire=True)
    employe = Employe(nom=nom, prenom=prenom, utilisateur=utilisateur)
    contrat = Contrat(employe=employe, heures_mensuelles=heures, date_debut=date_entree)
    _tracer(utilisateur, employe, contrat)
    db.session.add_all([utilisateur, employe, contrat])
    db.session.commit()
    return jsonify(employe.to_dict(avec_contrats=True)), 201


@employes_bp.route('/<int:employe_id>', methods=['GET'])
@admin_requis
def detail(employe_id):
    return jsonify(_get_employe(employe_id).to_dict(avec_contrats=True)), 200


@employes_bp.route('/<int:employe_id>', methods=['PUT'])
@admin_requis
def modifier(employe_id):
    employe = _get_employe(employe_id)
    data = donnees_json()
    employe.nom = texte(data, 'nom', longueur_max=100)
    employe.prenom = texte(data, 'prenom', longueur_max=100)
    if employe.utilisateur and 'identifiant' in data:
        identifiant = _identifiant(data)
        autre = Utilisateur.query.filter_by(identifiant=identifiant).first()
        if autre and autre.id != employe.utilisateur.id:
            raise ApiError('Cet identifiant est déjà utilisé', 409)
        employe.utilisateur.identifiant = identifiant
        _tracer(employe.utilisateur)
    _tracer(employe)
    db.session.commit()
    return jsonify(employe.to_dict(avec_contrats=True)), 200


@employes_bp.route('/<int:employe_id>/contrats', methods=['POST'])
@admin_requis
def nouveau_contrat(employe_id):
    """Avenant : clôt le contrat en cours la veille et ouvre le nouveau."""
    employe = _get_employe(employe_id)
    data = donnees_json()
    heures = parse_decimal(data.get('heures_mensuelles'), 'heures_mensuelles')
    date_debut = parse_date(data.get('date_debut'), 'date_debut')

    en_cours = employe.contrat_en_cours
    if en_cours is None:
        raise ApiError("Aucun contrat en cours : utilisez « Retour de l'employé »", 409)
    if date_debut <= en_cours.date_debut:
        raise ApiError('Le nouveau contrat doit commencer après le début du contrat en cours', 409)

    en_cours.date_fin = date_debut - timedelta(days=1)
    contrat = Contrat(employe=employe, heures_mensuelles=heures, date_debut=date_debut)
    _tracer(en_cours, contrat)
    db.session.add(contrat)
    db.session.commit()
    return jsonify(employe.to_dict(avec_contrats=True)), 201


@employes_bp.route('/<int:employe_id>/contrats/<int:contrat_id>', methods=['PUT'])
@admin_requis
def corriger_contrat(employe_id, contrat_id):
    employe = _get_employe(employe_id)
    contrat = next((c for c in employe.contrats if c.id == contrat_id), None)
    if contrat is None:
        raise ApiError('Contrat introuvable', 404)
    data = donnees_json()
    contrat.heures_mensuelles = parse_decimal(data.get('heures_mensuelles'), 'heures_mensuelles')
    contrat.date_debut = parse_date(data.get('date_debut'), 'date_debut')
    contrat.date_fin = parse_date(data.get('date_fin'), 'date_fin', obligatoire=False)
    if contrat.date_fin and contrat.date_fin < contrat.date_debut:
        raise ApiError('La date de fin doit être postérieure à la date de début')
    _tracer(contrat)
    db.session.commit()
    db.session.refresh(employe)
    return jsonify(employe.to_dict(avec_contrats=True)), 200


@employes_bp.route('/<int:employe_id>/contrats/<int:contrat_id>', methods=['DELETE'])
@admin_requis
def supprimer_contrat(employe_id, contrat_id):
    employe = _get_employe(employe_id)
    contrat = next((c for c in employe.contrats if c.id == contrat_id), None)
    if contrat is None:
        raise ApiError('Contrat introuvable', 404)
    if len(employe.contrats) == 1:
        raise ApiError("Impossible de supprimer le seul contrat de l'employé", 409)
    employe.contrats.remove(contrat)
    db.session.commit()
    return jsonify(employe.to_dict(avec_contrats=True)), 200


@employes_bp.route('/<int:employe_id>/depart', methods=['POST'])
@admin_requis
def depart(employe_id):
    employe = _get_employe(employe_id)
    data = donnees_json()
    date_sortie = parse_date(data.get('date_sortie'), 'date_sortie')
    en_cours = employe.contrat_en_cours
    if en_cours is None:
        raise ApiError("Cet employé n'a pas de contrat en cours", 409)
    if date_sortie < en_cours.date_debut:
        raise ApiError('La date de sortie doit être postérieure au début du contrat en cours', 409)

    en_cours.date_fin = date_sortie
    _tracer(en_cours)
    if employe.utilisateur:
        employe.utilisateur.actif = False
        employe.utilisateur.version_session += 1
        _tracer(employe.utilisateur)
    db.session.commit()
    return jsonify(employe.to_dict(avec_contrats=True)), 200


@employes_bp.route('/<int:employe_id>/retour', methods=['POST'])
@admin_requis
def retour(employe_id):
    employe = _get_employe(employe_id)
    data = donnees_json()
    date_entree = parse_date(data.get('date_entree'), 'date_entree')
    heures = parse_decimal(data.get('heures_mensuelles'), 'heures_mensuelles')
    mot_de_passe = _mot_de_passe_provisoire(data)

    if employe.contrat_en_cours is not None:
        raise ApiError('Cet employé a déjà un contrat en cours', 409)
    if employe.date_sortie and date_entree <= employe.date_sortie:
        raise ApiError('La date de retour doit être postérieure à la dernière date de sortie', 409)

    contrat = Contrat(employe=employe, heures_mensuelles=heures, date_debut=date_entree)
    db.session.add(contrat)
    if employe.utilisateur:
        employe.utilisateur.actif = True
        employe.utilisateur.definir_mot_de_passe(mot_de_passe, provisoire=True)
        _tracer(employe.utilisateur)
    _tracer(contrat)
    db.session.commit()
    db.session.refresh(employe)
    return jsonify(employe.to_dict(avec_contrats=True)), 200


@employes_bp.route('/<int:employe_id>/mot-de-passe', methods=['POST'])
@admin_requis
def reinitialiser_mot_de_passe(employe_id):
    employe = _get_employe(employe_id)
    if employe.utilisateur is None:
        raise ApiError("Cet employé n'a pas de compte", 409)
    if not employe.utilisateur.actif:
        raise ApiError('Ce compte est désactivé', 409)
    employe.utilisateur.definir_mot_de_passe(_mot_de_passe_provisoire(donnees_json()), provisoire=True)
    _tracer(employe.utilisateur)
    db.session.commit()
    return jsonify({'message': 'Mot de passe provisoire défini'}), 200
