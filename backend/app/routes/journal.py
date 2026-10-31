from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from flask import Blueprint, jsonify, request

from app.models import JournalModification
from app.securite import admin_requis
from app.utils import ApiError, bornes_mois

journal_bp = Blueprint('journal', __name__, url_prefix='/api/journal')

_FUSEAU = ZoneInfo('Europe/Paris')
_ROLES = ('admin', 'employe')


@journal_bp.route('', methods=['GET'])
@admin_requis
def lister():
    """Lecture seule : aucune route ne permet de modifier ou supprimer le journal."""
    query = JournalModification.query

    employe_id = request.args.get('employe_id', type=int)
    if employe_id:
        query = query.filter(JournalModification.employe_id == employe_id)
    if request.args.get('mois'):
        debut, fin = bornes_mois(request.args['mois'])
        # Mois de l'action, à l'heure de Paris.
        query = query.filter(
            JournalModification.cree_le >= datetime.combine(debut, time.min, _FUSEAU),
            JournalModification.cree_le < datetime.combine(fin + timedelta(days=1), time.min, _FUSEAU),
        )
    auteur = request.args.get('auteur')
    if auteur:
        if auteur not in _ROLES:
            raise ApiError('Auteur invalide')
        query = query.filter(JournalModification.auteur_role == auteur)
    type_ = request.args.get('type')
    if type_:
        if type_ not in JournalModification.TYPES:
            raise ApiError('Type invalide')
        query = query.filter(JournalModification.type == type_)

    page = max(request.args.get('page', 1, type=int), 1)
    par_page = min(max(request.args.get('par_page', 50, type=int), 1), 200)
    total = query.count()
    lignes = (
        query.order_by(JournalModification.cree_le.desc(), JournalModification.id.desc())
        .offset((page - 1) * par_page)
        .limit(par_page)
        .all()
    )
    return jsonify({'total': total, 'page': page, 'par_page': par_page, 'lignes': [l.to_dict() for l in lignes]}), 200
