from datetime import date, datetime
from zoneinfo import ZoneInfo

from app.services.feries import est_ferie
from app.utils import ApiError

_FUSEAU = ZoneInfo('Europe/Paris')
# Jusqu'à ce jour du mois (inclus), l'employé peut encore corriger les saisies du mois précédent.
JOUR_LIMITE_MOIS_PRECEDENT = 5


def aujourdhui():
    return datetime.now(_FUSEAU).date()


def modifiable_par_employe(jour, reference):
    """Mois en cours, ou mois précédent jusqu'au 5 inclus."""
    debut_mois = reference.replace(day=1)
    if (jour.year, jour.month) == (reference.year, reference.month):
        return True
    debut_precedent = date(debut_mois.year - (debut_mois.month == 1), (debut_mois.month - 2) % 12 + 1, 1)
    return reference.day <= JOUR_LIMITE_MOIS_PRECEDENT and debut_precedent <= jour < debut_mois


def verifier_jour_ouvert_employe(jour):
    """Un employé ne saisit ni le futur, ni un dimanche, ni un jour férié ou de fermeture."""
    from app.models import JourFermeture

    if jour > aujourdhui():
        raise ApiError('Impossible de saisir une date future.', 409, 'date_future')
    if jour.weekday() == 6:
        raise ApiError('Impossible de saisir un dimanche.', 409, 'dimanche')
    if est_ferie(jour):
        raise ApiError('Impossible de saisir un jour férié.', 409, 'jour_ferie')
    if JourFermeture.query.filter_by(date=jour).first():
        raise ApiError('Impossible de saisir un jour de fermeture de la pharmacie.', 409, 'jour_ferme')


def verifier_fenetre_employe(jour, phrase):
    """`phrase` : ex. « Les déplacements ne peuvent être saisis ou corrigés »."""
    if not modifiable_par_employe(jour, aujourdhui()):
        raise ApiError(
            f'{phrase} que pour le mois en cours '
            f'(et le mois précédent jusqu’au {JOUR_LIMITE_MOIS_PRECEDENT} inclus). Demandez à la pharmacienne.',
            403,
            'hors_periode',
        )
