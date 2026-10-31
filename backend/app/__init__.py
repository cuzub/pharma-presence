"""Fabrique de l'application Flask."""

import os

from flask import Flask, jsonify
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.proxy_fix import ProxyFix

from config import INSECURE_JWT_SECRET, INSECURE_SECRET, config
from app.extensions import db, jwt, limiter, migrate
from app.utils import ApiError

# Messages lisibles pour les contraintes PostgreSQL (voir la migration initiale).
_CONTRAINTES = {
    'ex_contrats_chevauchement': 'Les périodes de contrat de cet employé se chevauchent',
    'ex_absences_chevauchement': 'Cette absence chevauche une autre absence du même employé',
    'utilisateurs_identifiant_key': 'Cet identifiant est déjà utilisé',
    'uq_heures_employe_jour': 'Des heures sont déjà saisies pour ce jour',
}


def _verifier_production(app):
    if app.config['SECRET_KEY'] == INSECURE_SECRET or app.config['JWT_SECRET_KEY'] == INSECURE_JWT_SECRET:
        raise RuntimeError('SECRET_KEY et JWT_SECRET_KEY doivent être définis en production.')
    if len(app.config['JWT_SECRET_KEY']) < 32:
        raise RuntimeError('JWT_SECRET_KEY doit contenir au moins 32 caractères.')
    if not app.config['JWT_COOKIE_SECURE']:
        raise RuntimeError('JWT_COOKIE_SECURE doit être activé en production (HTTPS).')


def _enregistrer_erreurs(app):
    @app.errorhandler(ApiError)
    def _api_error(error):
        db.session.rollback()
        return error.to_response()

    @app.errorhandler(IntegrityError)
    def _integrity_error(error):
        db.session.rollback()
        detail = str(error.orig)
        for contrainte, message in _CONTRAINTES.items():
            if contrainte in detail:
                return jsonify({'message': message}), 409
        app.logger.warning('Violation de contrainte : %s', detail)
        return jsonify({'message': 'Données invalides ou incohérentes'}), 409

    @app.errorhandler(HTTPException)
    def _http_error(error):
        messages = {404: 'Ressource introuvable', 405: 'Méthode non autorisée', 429: 'Trop de tentatives, réessayez dans une minute'}
        return jsonify({'message': messages.get(error.code, error.description)}), error.code


def create_app(config_name=None):
    config_name = config_name or os.environ.get('FLASK_ENV', 'development')
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    if config_name == 'production':
        _verifier_production(app)

    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
    db.init_app(app)
    migrate.init_app(app, db, directory=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'migrations'))
    jwt.init_app(app)
    limiter.init_app(app)

    from app import securite  # noqa: F401  (enregistre les callbacks JWT)
    from app.cli import enregistrer_commandes
    from app.routes.absences import absences_bp
    from app.routes.auth import auth_bp
    from app.routes.deplacements import deplacements_bp
    from app.routes.employes import employes_bp
    from app.routes.journal import journal_bp
    from app.routes.mois import mois_bp
    from app.routes.saisie import saisie_bp
    from app.routes.statistiques import statistiques_bp

    for blueprint in (auth_bp, employes_bp, absences_bp, deplacements_bp, saisie_bp, mois_bp, journal_bp, statistiques_bp):
        app.register_blueprint(blueprint)
    _enregistrer_erreurs(app)
    enregistrer_commandes(app)

    @app.route('/api/health')
    @limiter.exempt
    def health():
        return {'status': 'OK', 'version': os.environ.get('APP_VERSION', 'dev')}, 200

    @app.after_request
    def _entetes_securite(response):
        response.headers.setdefault('X-Content-Type-Options', 'nosniff')
        response.headers.setdefault('Cache-Control', 'no-store')
        return response

    return app
