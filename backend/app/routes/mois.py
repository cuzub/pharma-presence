from flask import Blueprint, Response, jsonify
from flask_jwt_extended import current_user

from app.securite import admin_requis, connexion_requise, employe_courant_id
from app.services.export import generer_csv_recap, generer_excel
from app.services.mois import controles, donnees_mois, serialiser_mois
from app.utils import ApiError, bornes_mois

mois_bp = Blueprint('mois', __name__, url_prefix='/api')

_XLSX = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'


@mois_bp.route('/mois/<mois>', methods=['GET'])
@connexion_requise()
def mois_detail(mois):
    """Admin : tous les employés concernés par le mois. Employé : uniquement lui-même."""
    debut, fin = bornes_mois(mois)
    employe_id = None if current_user.est_admin else employe_courant_id()
    lignes = donnees_mois(debut, fin, employe_id)
    return jsonify(serialiser_mois(debut, fin, lignes)), 200


@mois_bp.route('/exports/<mois>/controles', methods=['GET'])
@admin_requis
def export_controles(mois):
    debut, fin = bornes_mois(mois)
    return jsonify(controles(debut, fin, donnees_mois(debut, fin, pour_export=True))), 200


def _lignes_exportables(mois):
    debut, fin = bornes_mois(mois)
    lignes = donnees_mois(debut, fin, pour_export=True)
    resultat = controles(debut, fin, lignes)
    if resultat['bloquants']:
        raise ApiError(
            'Export impossible : ' + ' ; '.join(resultat['bloquants']), 409, 'controles_bloquants'
        )
    return debut, fin, lignes


def _fichier(contenu, nom, mimetype):
    return Response(
        contenu,
        mimetype=mimetype,
        headers={'Content-Disposition': f'attachment; filename="{nom}"', 'Cache-Control': 'no-store'},
    )


@mois_bp.route('/exports/<mois>/etat-preparatoire.xlsx', methods=['GET'])
@admin_requis
def export_excel(mois):
    debut, fin, lignes = _lignes_exportables(mois)
    return _fichier(generer_excel(debut, fin, lignes), f'etat-preparatoire-{mois}.xlsx', _XLSX)


@mois_bp.route('/exports/<mois>/recap.csv', methods=['GET'])
@admin_requis
def export_csv_recap(mois):
    debut, fin, lignes = _lignes_exportables(mois)
    return _fichier(generer_csv_recap(debut, fin, lignes), f'recap-{mois}.csv', 'text/csv; charset=utf-8')
