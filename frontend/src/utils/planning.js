// Planning de présence prévisionnel : demi-journées, remplissage des cases, présents et totaux par semaine.
import { absenceDuJour, jourSemaine } from './dates'

// Mêmes plages que le serveur (app/services/planning.py). Pause de 12h30 à 13h30.
export const PLAGES = { matin: ['09:00', '12:30'], apres_midi: ['13:30', '19:30'] }
export const DEMI_JOURNEES = ['matin', 'apres_midi']
export const LIBELLES_DEMI_JOURNEE = { matin: 'Matin', apres_midi: 'Après-midi' }
export const COULEUR_ABSENCE = '#9e9e9e'
export const SAMEDI = 5

export const minutesDe = (heure) => {
  const [h, m] = heure.split(':').map(Number)
  return h * 60 + m
}

// Demi-journées affichées pour un jour : le samedi n'a pas d'après-midi.
export const demiJourneesDuJour = (iso) => (jourSemaine(iso) === SAMEDI ? ['matin'] : DEMI_JOURNEES)

// Remplit la case au prorata : blanc hors présence, couleur de la personne pendant sa présence.
export const fondDemiJournee = (horaire, demi, couleur) => {
  if (!horaire) return null
  const [debutPlage, finPlage] = PLAGES[demi].map(minutesDe)
  const duree = finPlage - debutPlage
  const debut = ((minutesDe(horaire[0]) - debutPlage) / duree) * 100
  const fin = ((minutesDe(horaire[1]) - debutPlage) / duree) * 100
  const arrondi = (n) => Math.round(Math.min(100, Math.max(0, n)) * 10) / 10
  return `linear-gradient(to right, transparent ${arrondi(debut)}%, ${couleur} ${arrondi(debut)}%, ${couleur} ${arrondi(fin)}%, transparent ${arrondi(fin)}%)`
}

// 09:00 → « 9h », 14:30 → « 14h30 ».
export const formatHeure = (heure) => {
  const [h, m] = heure.split(':')
  return m === '00' ? `${Number(h)}h` : `${Number(h)}h${m}`
}

export const texteHoraire = (horaire) => (horaire ? `${formatHeure(horaire[0])}–${formatHeure(horaire[1])}` : '')

export const lignesHoraires = (entree) => {
  if (!entree) return []
  const lignes = DEMI_JOURNEES.filter((d) => entree[d]).map((d) => `${LIBELLES_DEMI_JOURNEE[d]} : ${texteHoraire(entree[d])}`)
  if (entree.exception) lignes.push(lignes.length ? 'Horaire exceptionnel' : 'Horaire exceptionnel : pas présent(e)')
  return lignes
}

// 2130 → « 35h30 », 0 → « 0h ».
export const formatDuree = (minutes) => {
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  return m ? `${h}h${String(m).padStart(2, '0')}` : `${h}h`
}

// Une personne compte dans les présents si le planning la prévoit et qu'elle n'est pas absente ce jour-là.
export const estPresent = (personne, iso, demi) =>
  !!personne.planning?.[iso]?.[demi] && !absenceDuJour(personne.absences || [], iso)

// Présent à la fermeture d'une demi-journée (12h30 ou 19h30) : non absent et horaire prévu jusqu'à cette heure au moins.
export const presentsFermeture = (personnes, iso, demi) => {
  const fermeture = minutesDe(PLAGES[demi][1])
  return personnes.filter((p) => estPresent(p, iso, demi) && minutesDe(p.planning[iso][demi][1]) >= fermeture).length
}

// Seuil vide (null) : jamais d'alerte.
export const sousSeuilFermeture = (nombre, iso, seuils) => {
  const seuil = jourSemaine(iso) === SAMEDI ? seuils?.seuil_samedi : seuils?.seuil_semaine
  return seuil != null && nombre < seuil
}

// Numéro de semaine ISO 8601.
export const numeroSemaine = (iso) => {
  const [a, m, j] = iso.split('-').map(Number)
  const date = new Date(Date.UTC(a, m - 1, j))
  const jour = date.getUTCDay() || 7
  date.setUTCDate(date.getUTCDate() + 4 - jour)
  const debutAnnee = new Date(Date.UTC(date.getUTCFullYear(), 0, 1))
  return Math.ceil(((date - debutAnnee) / 86400000 + 1) / 7)
}
