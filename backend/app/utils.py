import calendar
import re
from datetime import date
from decimal import Decimal, InvalidOperation

from flask import jsonify, request


class ApiError(Exception):
    def __init__(self, message, status=400, code=None):
        super().__init__(message)
        self.message = message
        self.status = status
        self.code = code

    def to_response(self):
        payload = {'message': self.message}
        if self.code:
            payload['code'] = self.code
        return jsonify(payload), self.status


def donnees_json():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ApiError('Données JSON attendues')
    return data


def texte(data, cle, obligatoire=True, longueur_max=255):
    valeur = data.get(cle)
    valeur = valeur.strip() if isinstance(valeur, str) else ''
    if obligatoire and not valeur:
        raise ApiError(f'Champ « {cle} » obligatoire')
    if len(valeur) > longueur_max:
        raise ApiError(f'Champ « {cle} » trop long ({longueur_max} caractères maximum)')
    return valeur or None


def parse_date(valeur, cle='date', obligatoire=True):
    if valeur in (None, ''):
        if obligatoire:
            raise ApiError(f'Champ « {cle} » obligatoire')
        return None
    try:
        return date.fromisoformat(str(valeur))
    except ValueError:
        raise ApiError(f'Date invalide pour « {cle} » (format AAAA-MM-JJ attendu)')


def parse_decimal(valeur, cle, minimum_exclu=Decimal('0')):
    try:
        nombre = Decimal(str(valeur).replace(',', '.'))
    except (InvalidOperation, ValueError):
        raise ApiError(f'Nombre invalide pour « {cle} »')
    if not nombre.is_finite() or nombre <= minimum_exclu:
        raise ApiError(f'« {cle} » doit être supérieur à {minimum_exclu}')
    return nombre


_MOIS_RE = re.compile(r'^(\d{4})-(\d{2})$')


def bornes_mois(mois):
    """'2025-01' -> (date(2025, 1, 1), date(2025, 1, 31))."""
    match = _MOIS_RE.match(mois or '')
    if not match:
        raise ApiError('Mois invalide (format AAAA-MM attendu)')
    annee, numero = int(match.group(1)), int(match.group(2))
    if not 1 <= numero <= 12 or not 2000 <= annee <= 2100:
        raise ApiError('Mois invalide (format AAAA-MM attendu)')
    return date(annee, numero, 1), date(annee, numero, calendar.monthrange(annee, numero)[1])


def format_date_fr(valeur):
    return valeur.strftime('%d/%m/%Y') if valeur else ''
