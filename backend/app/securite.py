from functools import wraps

from flask import jsonify
from flask_jwt_extended import current_user, verify_jwt_in_request

from app.extensions import db, jwt
from app.models import Utilisateur
from app.utils import ApiError


def _non_authentifie(_raison=None):
    return jsonify({'message': 'Session expirée ou invalide, veuillez vous reconnecter', 'code': 'non_authentifie'}), 401


@jwt.user_identity_loader
def _identite(utilisateur):
    return str(utilisateur.id)


@jwt.additional_claims_loader
def _claims(utilisateur):
    return {'sv': utilisateur.version_session}


@jwt.user_lookup_loader
def _charger_utilisateur(_header, payload):
    utilisateur = db.session.get(Utilisateur, int(payload['sub']))
    # Un compte désactivé ou dont le mot de passe a changé n'a plus accès, même avec un jeton valide.
    if utilisateur is None or not utilisateur.actif or payload.get('sv') != utilisateur.version_session:
        return None
    return utilisateur


jwt.user_lookup_error_loader(lambda _h, _p: _non_authentifie())
jwt.unauthorized_loader(_non_authentifie)
jwt.invalid_token_loader(_non_authentifie)
jwt.expired_token_loader(lambda _h, _p: _non_authentifie())


def connexion_requise(admin=False, autoriser_mdp_provisoire=False):
    def decorateur(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            if current_user.doit_changer_mdp and not autoriser_mdp_provisoire:
                raise ApiError('Vous devez changer votre mot de passe provisoire', 403, 'changement_mdp_requis')
            if admin and not current_user.est_admin:
                raise ApiError('Accès réservé à la pharmacienne', 403, 'acces_refuse')
            return fn(*args, **kwargs)

        return wrapper

    return decorateur


def admin_requis(fn):
    return connexion_requise(admin=True)(fn)


def employe_courant_id():
    """Identifiant d'employé de l'utilisateur connecté (déduit de la session, jamais du client)."""
    if current_user.employe is None:
        raise ApiError('Aucune fiche employé associée à ce compte', 403, 'acces_refuse')
    return current_user.employe.id


def verifier_mot_de_passe_valide(mot_de_passe, longueur_min):
    if not isinstance(mot_de_passe, str) or len(mot_de_passe) < longueur_min or not mot_de_passe.strip():
        raise ApiError(f'Le mot de passe doit contenir au moins {longueur_min} caractères')
