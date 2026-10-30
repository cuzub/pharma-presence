from datetime import datetime, timezone

from flask import Blueprint, current_app, jsonify
from flask_jwt_extended import create_access_token, current_user, set_access_cookies, unset_jwt_cookies

from app.extensions import db, limiter
from app.models import Utilisateur
from app.securite import connexion_requise, verifier_mot_de_passe_valide
from app.utils import ApiError, donnees_json

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


def _reponse_session(utilisateur, status=200):
    response = jsonify(utilisateur.to_dict())
    set_access_cookies(response, create_access_token(identity=utilisateur))
    return response, status


@auth_bp.route('/login', methods=['POST'])
@limiter.limit(lambda: current_app.config['RATELIMIT_AUTH_LOGIN'])
def login():
    data = donnees_json()
    identifiant = (data.get('identifiant') or '').strip().lower()
    mot_de_passe = data.get('mot_de_passe') or ''
    if not identifiant or not mot_de_passe:
        raise ApiError('Identifiant et mot de passe obligatoires')

    utilisateur = Utilisateur.query.filter_by(identifiant=identifiant).first()
    if utilisateur is None or not utilisateur.verifier_mot_de_passe(mot_de_passe) or not utilisateur.actif:
        raise ApiError('Identifiant ou mot de passe incorrect', 401, 'identifiants_invalides')

    utilisateur.derniere_connexion = datetime.now(timezone.utc)
    db.session.commit()
    return _reponse_session(utilisateur)


@auth_bp.route('/logout', methods=['POST'])
def logout():
    response = jsonify({'message': 'Déconnecté'})
    unset_jwt_cookies(response)
    return response, 200


@auth_bp.route('/me', methods=['GET'])
@connexion_requise(autoriser_mdp_provisoire=True)
def me():
    return jsonify(current_user.to_dict()), 200


@auth_bp.route('/mot-de-passe', methods=['POST'])
@connexion_requise(autoriser_mdp_provisoire=True)
def changer_mot_de_passe():
    data = donnees_json()
    actuel = data.get('mot_de_passe_actuel') or ''
    nouveau = data.get('nouveau_mot_de_passe') or ''
    if not current_user.verifier_mot_de_passe(actuel):
        raise ApiError('Mot de passe actuel incorrect', 400, 'mot_de_passe_actuel_incorrect')
    verifier_mot_de_passe_valide(nouveau, current_app.config['MOT_DE_PASSE_LONGUEUR_MIN'])
    if nouveau == actuel:
        raise ApiError('Le nouveau mot de passe doit être différent de l’actuel')

    current_user.definir_mot_de_passe(nouveau, provisoire=False)
    current_user.updated_by_id = current_user.id
    db.session.commit()
    # Nouvelle session : l'ancienne est invalidée par l'incrément de version_session.
    return _reponse_session(current_user)
