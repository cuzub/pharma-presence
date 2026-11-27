"""Planning de présence prévisionnel : une trame semaine 1 / semaine 2 par personne, exceptions à la journée, totaux par semaine.

Le planning est une prévision : il n'alimente ni les heures +/- ni l'export comptable.
"""

import re
from collections import defaultdict
from datetime import timedelta

from app.models import ExceptionPlanning, TramePlanning
from app.utils import ApiError

COULEUR_ADMIN = '#00bcd4'
DEMI_JOURNEES = ('matin', 'apres_midi')
# Plages de chaque demi-journée (échelle d'affichage et bornes de saisie). Pause de 12h30 à 13h30.
PLAGES = {'matin': ('09:00', '12:30'), 'apres_midi': ('13:30', '19:30')}
LIBELLES = {'matin': 'matin', 'apres_midi': 'après-midi'}
JOURS = ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi']
SAMEDI = 5

_HEURE_RE = re.compile(r'^([01]\d|2[0-3]):([0-5]\d)$')


def _minutes(heure):
    h, m = heure.split(':')
    return int(h) * 60 + int(m)


def _demi_journee(valeur, cle, contexte):
    """None / [] / ['', ''] → None ; sinon ['HH:MM', 'HH:MM'] validé dans la plage, par tranche de 5 min."""
    if valeur in (None, '', []):
        return None
    if not isinstance(valeur, (list, tuple)) or len(valeur) != 2:
        raise ApiError(f'{contexte} : horaire du {LIBELLES[cle]} invalide')
    if all(v in (None, '') for v in valeur):
        return None
    if not all(isinstance(v, str) and _HEURE_RE.match(v) for v in valeur):
        raise ApiError(f'{contexte} : heures du {LIBELLES[cle]} invalides (format HH:MM attendu, début et fin)')
    debut, fin = (_minutes(v) for v in valeur)
    if debut % 5 or fin % 5:
        raise ApiError(f'{contexte} : les heures se saisissent par tranche de 5 minutes')
    plage_debut, plage_fin = (_minutes(v) for v in PLAGES[cle])
    if not plage_debut <= debut < fin <= plage_fin:
        raise ApiError(
            f'{contexte} : le {LIBELLES[cle]} doit être compris entre {PLAGES[cle][0]} et {PLAGES[cle][1]} '
            '(début avant fin)'
        )
    return [valeur[0], valeur[1]]


def valider_jour(data, jour_semaine, contexte):
    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise ApiError(f'{contexte} : horaires invalides')
    horaires = {cle: _demi_journee(data.get(cle), cle, contexte) for cle in DEMI_JOURNEES}
    if jour_semaine == SAMEDI and horaires['apres_midi']:
        raise ApiError(f'{contexte} : pas d’après-midi le samedi')
    if jour_semaine > SAMEDI and any(horaires.values()):
        raise ApiError(f'{contexte} : pas de planning le dimanche')
    return horaires


def valider_horaires_trame(data):
    if not isinstance(data, dict):
        raise ApiError('Horaires de la trame invalides')
    resultat = {}
    for semaine in ('1', '2'):
        jours = data.get(semaine)
        if not isinstance(jours, list) or len(jours) != len(JOURS):
            raise ApiError(f'Semaine {semaine} : un horaire par jour du lundi au samedi attendu')
        resultat[semaine] = [
            valider_jour(jour, index, f'Semaine {semaine}, {JOURS[index]}') for index, jour in enumerate(jours)
        ]
    return resultat


def semaine_type(jour):
    """Semaine 1 = semaine ISO impaire, semaine 2 = semaine ISO paire."""
    return '1' if jour.isocalendar().week % 2 else '2'


def minutes_jour(horaires):
    return sum(_minutes(h[1]) - _minutes(h[0]) for h in (horaires.get(c) for c in DEMI_JOURNEES) if h)


def bornes_semaines(debut, fin):
    """Du lundi de la première semaine au samedi de la dernière (les totaux portent sur des semaines entières)."""
    return debut - timedelta(days=debut.weekday()), fin - timedelta(days=fin.weekday()) + timedelta(days=SAMEDI)


def _filtre_titulaire(modele, champ, ids):
    return modele.query.filter(getattr(modele, champ).in_(ids))


def plannings(debut, fin, employe_ids=(), utilisateur_ids=()):
    """Horaires prévus jour par jour (lundi → samedi) pour chaque titulaire.

    Renvoie {('employe', id) | ('admin', id): {date: {'matin', 'apres_midi', 'exception'}}} ; les jours sans présence
    ni exception sont omis.
    """
    trames = {}
    exceptions = defaultdict(dict)
    for champ, ids, genre in (('employe_id', employe_ids, 'employe'), ('utilisateur_id', utilisateur_ids, 'admin')):
        if not ids:
            continue
        for trame in _filtre_titulaire(TramePlanning, champ, ids):
            trames[(genre, getattr(trame, champ))] = trame
        requete = _filtre_titulaire(ExceptionPlanning, champ, ids).filter(ExceptionPlanning.jour.between(debut, fin))
        for exception in requete:
            exceptions[(genre, getattr(exception, champ))][exception.jour] = exception

    cles = [('employe', i) for i in employe_ids] + [('admin', i) for i in utilisateur_ids]
    resultat = {}
    for cle in cles:
        jours = {}
        trame = trames.get(cle)
        jour = debut
        while jour <= fin:
            if jour.weekday() <= SAMEDI:
                exception = exceptions[cle].get(jour)
                if exception is not None:
                    jours[jour] = {**_normaliser(exception.horaires), 'exception': True}
                elif trame is not None:
                    horaires = _normaliser(trame.horaires[semaine_type(jour)][jour.weekday()])
                    if any(horaires.values()):
                        jours[jour] = {**horaires, 'exception': False}
            jour += timedelta(days=1)
        resultat[cle] = jours
    return resultat


def _normaliser(horaires):
    return {cle: (horaires or {}).get(cle) for cle in DEMI_JOURNEES}


def totaux_semaines(jours, debut, fin, jour_compte=lambda jour: True):
    """Minutes prévues par semaine (clé : lundi ISO), absences non déduites. `jour_compte` exclut p. ex. les jours hors contrat."""
    totaux = {}
    lundi = debut
    while lundi <= fin:
        totaux[lundi.isoformat()] = sum(
            minutes_jour(jours[lundi + timedelta(days=n)])
            for n in range(SAMEDI + 1)
            if lundi + timedelta(days=n) in jours and jour_compte(lundi + timedelta(days=n))
        )
        lundi += timedelta(days=7)
    return totaux


def serialiser_jours(jours):
    return {jour.isoformat(): valeur for jour, valeur in sorted(jours.items())}
