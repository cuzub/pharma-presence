// Dates manipulées au format ISO « AAAA-MM-JJ » (sans fuseau horaire) pour éviter tout décalage.

export const MOIS_FR = [
  'janvier', 'février', 'mars', 'avril', 'mai', 'juin',
  'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'
]
export const JOURS_COURTS = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']

const pad = (n) => String(n).padStart(2, '0')

export const iso = (annee, mois, jour) => `${annee}-${pad(mois)}-${pad(jour)}`

export const isoDepuisDate = (date) => iso(date.getFullYear(), date.getMonth() + 1, date.getDate())

export const dateDepuisIso = (valeur) => {
  const [annee, mois, jour] = valeur.split('-').map(Number)
  return new Date(annee, mois - 1, jour)
}

export const aujourdhuiIso = () => isoDepuisDate(new Date())

export const ajouterJours = (valeur, n) => {
  const date = dateDepuisIso(valeur)
  date.setDate(date.getDate() + n)
  return isoDepuisDate(date)
}

export const formatFr = (valeur) => {
  if (!valeur) return ''
  const [annee, mois, jour] = valeur.split('-')
  return `${jour}/${mois}/${annee}`
}

// --- Mois « AAAA-MM » -------------------------------------------------------

export const moisCourant = () => aujourdhuiIso().slice(0, 7)

export const estMoisValide = (mois) => /^\d{4}-(0[1-9]|1[0-2])$/.test(mois || '')

// --- Années ------------------------------------------------------------------

export const anneeCourante = () => new Date().getFullYear()

export const decalerMois = (mois, delta) => {
  const [annee, numero] = mois.split('-').map(Number)
  const date = new Date(annee, numero - 1 + delta, 1)
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}`
}

export const libelleMois = (mois) => {
  const [annee, numero] = mois.split('-').map(Number)
  return `${MOIS_FR[numero - 1]} ${annee}`
}

export const joursDuMois = (mois) => {
  const [annee, numero] = mois.split('-').map(Number)
  const nombre = new Date(annee, numero, 0).getDate()
  return Array.from({ length: nombre }, (_, i) => iso(annee, numero, i + 1))
}

// 0 = lundi … 6 = dimanche
export const jourSemaine = (valeur) => (dateDepuisIso(valeur).getDay() + 6) % 7

// --- Jours fériés (France métropolitaine) -----------------------------------

// Date de Pâques (algorithme de Meeus/Jones/Butcher, calendrier grégorien).
export const paques = (annee) => {
  const a = annee % 19
  const b = Math.floor(annee / 100)
  const c = annee % 100
  const d = Math.floor(b / 4)
  const e = b % 4
  const f = Math.floor((b + 8) / 25)
  const g = Math.floor((b - f + 1) / 3)
  const h = (19 * a + b - d - g + 15) % 30
  const i = Math.floor(c / 4)
  const k = c % 4
  const l = (32 + 2 * e + 2 * i - h - k) % 7
  const m = Math.floor((a + 11 * h + 22 * l) / 451)
  const mois = Math.floor((h + l - 7 * m + 114) / 31)
  const jour = ((h + l - 7 * m + 114) % 31) + 1
  return iso(annee, mois, jour)
}

const cacheFeries = new Map()

export const joursFeries = (annee) => {
  if (!cacheFeries.has(annee)) {
    const p = paques(annee)
    cacheFeries.set(annee, new Map([
      [iso(annee, 1, 1), 'Jour de l’an'],
      [ajouterJours(p, 1), 'Lundi de Pâques'],
      [iso(annee, 5, 1), 'Fête du Travail'],
      [iso(annee, 5, 8), 'Victoire 1945'],
      [ajouterJours(p, 39), 'Ascension'],
      [ajouterJours(p, 50), 'Lundi de Pentecôte'],
      [iso(annee, 7, 14), 'Fête nationale'],
      [iso(annee, 8, 15), 'Assomption'],
      [iso(annee, 11, 1), 'Toussaint'],
      [iso(annee, 11, 11), 'Armistice 1918'],
      [iso(annee, 12, 25), 'Noël']
    ]))
  }
  return cacheFeries.get(annee)
}

export const ferie = (valeur) => joursFeries(Number(valeur.slice(0, 4))).get(valeur) || null

// --- Absences ----------------------------------------------------------------

// Une absence couvre ses jours du premier jour d'absence (inclus) au jour de reprise (exclu).
export const absenceCouvre = (absence, jour) =>
  absence.date_debut <= jour && (!absence.date_reprise || jour < absence.date_reprise)

export const absenceDuJour = (absences, jour) => absences.find((a) => absenceCouvre(a, jour)) || null

// Une absence bloque la saisie d'heures et de déplacements si son motif le demande.
export const absenceBloquanteDuJour = (absences, jour) =>
  absences.find((a) => a.motif_bloque_saisie && absenceCouvre(a, jour)) || null

export const formatNombre = (valeur) => {
  if (valeur === null || valeur === undefined || valeur === '') return ''
  return Number(valeur).toLocaleString('fr-FR', { maximumFractionDigits: 2 })
}

// --- Heures en plus / en moins (minutes signées) ----------------------------

// +90 → « +1h30 », -30 → « -30min », +120 → « +2h ».
export const formatMinutes = (minutes) => {
  if (!minutes) return ''
  const signe = minutes < 0 ? '-' : '+'
  const total = Math.abs(minutes)
  const heures = Math.floor(total / 60)
  const reste = total % 60
  if (!heures) return `${signe}${reste}min`
  return reste ? `${signe}${heures}h${String(reste).padStart(2, '0')}` : `${signe}${heures}h`
}

// --- Régularisations (crédit / débit d'heures +/-) ---------------------------

// Crédit de 2 h 30 → 150 ; débit de 20 h → -1200. Renvoie null si la durée est nulle ou invalide.
export const minutesRegularisation = (sens, heures, minutes) => {
  const h = Number(heures || 0)
  const m = Number(minutes || 0)
  if (!Number.isInteger(h) || !Number.isInteger(m) || h < 0 || m < 0 || m > 59) return null
  const total = h * 60 + m
  if (!total) return null
  return sens === 'debit' ? -total : total
}

export const titreRegularisation = (r) =>
  `Régularisation ${formatMinutes(r.minutes)}${r.commentaire ? ` — ${r.commentaire}` : ''}`

// --- Saisies de l'employé (heures +/- et déplacements) ----------------------

// Même règle que le serveur : mois en cours, ou mois précédent jusqu'au 5 inclus.
export const JOUR_LIMITE_MOIS_PRECEDENT = 5

export const saisieModifiableParEmploye = (jour, reference = aujourdhuiIso()) => {
  const moisReference = reference.slice(0, 7)
  if (jour.slice(0, 7) === moisReference) return true
  return Number(reference.slice(8)) <= JOUR_LIMITE_MOIS_PRECEDENT && jour.slice(0, 7) === decalerMois(moisReference, -1)
}
