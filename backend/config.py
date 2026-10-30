import os
from datetime import timedelta
from urllib.parse import quote_plus


def _env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ('1', 'true', 'yes', 'on')


def _database_uri(default):
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        return database_url

    postgres_password = os.environ.get('POSTGRES_PASSWORD')
    if postgres_password:
        user = quote_plus(os.environ.get('POSTGRES_USER', 'presence'))
        password = quote_plus(postgres_password)
        host = os.environ.get('POSTGRES_HOST', 'db')
        port = os.environ.get('POSTGRES_PORT', '5432')
        database = quote_plus(os.environ.get('POSTGRES_DB', 'presence'))
        return f'postgresql://{user}:{password}@{host}:{port}/{database}'

    return default


INSECURE_SECRET = 'dev-secret-change-me'
INSECURE_JWT_SECRET = 'dev-jwt-secret-change-me-in-production-please'


class Config:
    SQLALCHEMY_DATABASE_URI = _database_uri('postgresql://presence:presence@localhost:5433/presence')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY') or INSECURE_SECRET
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or INSECURE_JWT_SECRET

    # Session JWT stockée dans un cookie httpOnly (jamais lisible par le JavaScript),
    # protégée contre le CSRF par le double cookie de Flask-JWT-Extended.
    JWT_TOKEN_LOCATION = ['cookies']
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.environ.get('SESSION_HOURS', '8')))
    JWT_COOKIE_SECURE = _env_bool('JWT_COOKIE_SECURE', True)
    JWT_COOKIE_SAMESITE = 'Strict'
    JWT_COOKIE_CSRF_PROTECT = True
    JWT_ACCESS_COOKIE_PATH = '/api/'
    JWT_SESSION_COOKIE = True

    MOT_DE_PASSE_LONGUEUR_MIN = 12

    RATELIMIT_STORAGE_URI = os.environ.get('RATELIMIT_STORAGE_URI', 'memory://')
    RATELIMIT_HEADERS_ENABLED = True
    RATELIMIT_DEFAULT = os.environ.get('RATELIMIT_DEFAULT', '300 per minute')
    RATELIMIT_AUTH_LOGIN = os.environ.get('RATELIMIT_AUTH_LOGIN', '5 per minute')


class DevelopmentConfig(Config):
    ENV_NAME = 'development'
    DEBUG = True
    JWT_COOKIE_SECURE = _env_bool('JWT_COOKIE_SECURE', False)


class ProductionConfig(Config):
    ENV_NAME = 'production'
    DEBUG = False


class TestingConfig(Config):
    ENV_NAME = 'testing'
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'TEST_DATABASE_URL', 'postgresql://presence:presence@localhost:5433/presence_test'
    )
    JWT_COOKIE_SECURE = False
    JWT_SECRET_KEY = 'cle-de-test-suffisamment-longue-pour-hs256'
    RATELIMIT_ENABLED = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
}
