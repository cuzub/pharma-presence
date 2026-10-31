from datetime import date, timedelta
from functools import lru_cache


def _paques(annee):
    """Dimanche de Pâques (algorithme de Meeus/Jones/Butcher)."""
    a = annee % 19
    b, c = divmod(annee, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mois, jour = divmod(h + l - 7 * m + 114, 31)
    return date(annee, mois, jour + 1)


@lru_cache(maxsize=None)
def jours_feries(annee):
    paques = _paques(annee)
    return frozenset({
        date(annee, 1, 1),
        paques + timedelta(days=1),
        date(annee, 5, 1),
        date(annee, 5, 8),
        paques + timedelta(days=39),
        paques + timedelta(days=50),
        date(annee, 7, 14),
        date(annee, 8, 15),
        date(annee, 11, 1),
        date(annee, 11, 11),
        date(annee, 12, 25),
    })


def est_ferie(jour):
    return jour in jours_feries(jour.year)
