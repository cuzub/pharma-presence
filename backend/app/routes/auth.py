from datetime import datetime, timezone

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import (
    create_access_token, current_user, get_current_user, set_access_cookies, unset_jwt_cookies, verify_jwt_in_request,
)
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db, limiter
from app.models import Utilisateur
from app.securite import connexion_requise, verifier_mot_de_passe_valide
from app.utils import ApiError, donnees_json

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

_HASH_FACTICE = None


def _verifier_hash_factice(mot_de_passe):
    """Identifiant inconnu : même calcul qu'un vrai compte, pour ne pas révéler les identifiants existants."""
    global _HASH_FACTICE
    if _HASH_FACTICE is None:
        _HASH_FACTICE = generate_password_hash('mot-de-passe-factice')
    check_password_hash(_HASH_FACTICE, mot_de_passe)


def _identifiant_tente():
    data = request.get_json(silent=True)
    identifiant = data.get('identifiant') if isinstance(data, dict) else None
    return f"compte:{(identifiant or '').strip().lower()[:80]}" if isinstance(identifiant, str) else 'compte:'


def _reponse_session(utilisateur, status=200):
    response = jsonify(utilisateur.to_dict())
    set_access_cookies(response, create_access_token(identity=utilisateur))
    return response, status


@auth_bp.route('/login', methods=['POST'])
@limiter.limit(lambda: current_app.config['RATELIMIT_AUTH_LOGIN'])
# Par compte, seuls les échecs comptent : freine les essais répartis sur plusieurs adresses IP.
@limiter.limit(
    lambda: current_app.config['RATELIMIT_AUTH_COMPTE'],
    key_func=_identifiant_tente,
    deduct_when=lambda response: response.status_code == 401,
)
def login():
    data = donnees_json()
    identifiant = (data.get('identifiant') or '').strip().lower()
    mot_de_passe = data.get('mot_de_passe') or ''
    if not identifiant or not mot_de_passe:
        raise ApiError('Identifiant et mot de passe obligatoires')

    utilisateur = Utilisateur.query.filter_by(identifiant=identifiant).first()
    if utilisateur is None:
        _verifier_hash_factice(mot_de_passe)
    if utilisateur is None or not utilisateur.verifier_mot_de_passe(mot_de_passe) or not utilisateur.actif:
        raise ApiError('Identifiant ou mot de passe incorrect', 401, 'identifiants_invalides')

    utilisateur.derniere_connexion = datetime.now(timezone.utc)
    db.session.commit()
    return _reponse_session(utilisateur)


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Révoque la session côté serveur (le jeton volé ou resté sur un poste partagé devient inutilisable)."""
    try:
        verify_jwt_in_request(optional=True)
        utilisateur = get_current_user()
    except Exception:  # Jeton expiré, invalide ou sans CSRF : on se contente d'effacer les cookies.
        utilisateur = None
    if utilisateur is not None:
        utilisateur.version_session = (utilisateur.version_session or 0) + 1
        db.session.commit()
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
