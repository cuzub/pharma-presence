from flask import Blueprint, jsonify

from app.securite import admin_requis
from app.services.statistiques import statistiques_annee
from app.utils import ApiError

statistiques_bp = Blueprint('statistiques', __name__, url_prefix='/api/statistiques')


@statistiques_bp.route('/<int:annee>', methods=['GET'])
@admin_requis
def consulter(annee):
    if not 2000 <= annee <= 2100:
        raise ApiError('Année invalide (entre 2000 et 2100)')
    return jsonify(statistiques_annee(annee)), 200
