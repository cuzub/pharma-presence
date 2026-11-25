import { computed, ref } from 'vue'

// Chaque étape pointe un élément de la page par son attribut data-visite.
const ETAPES_EMPLOYE = [
  {
    cible: 'calendrier',
    titre: 'Votre calendrier du mois',
    texte: 'Chaque case est un jour. Vous y voyez vos horaires prévus, vos heures en plus ou en moins et vos déplacements.'
  },
  {
    cible: 'jour',
    titre: 'Cliquez sur une date pour saisir',
    texte: 'Une fenêtre s’ouvre : touchez un bouton rapide (+15 min, +30 min…) puis « Enregistrer ». Vous pouvez aussi déclarer un déplacement.'
  },
  {
    cible: 'resume',
    titre: 'Votre solde d’heures',
    texte: 'Le résumé donne le net du mois et votre solde cumulé d’heures en plus ou en moins.'
  },
  {
    cible: 'nav-/guide',
    titre: 'Une question ?',
    texte: 'Le guide d’utilisation explique chaque action pas à pas.'
  },
  {
    cible: 'visite',
    titre: 'À revoir quand vous voulez',
    texte: 'Ce bouton relance la visite à tout moment.'
  }
]

const ETAPES_ADMIN = [
  {
    cible: 'nav-/',
    titre: 'Le tableau du mois',
    texte: 'Tous les employés sur un mois : horaires prévus, absences, heures en plus ou en moins, km. Un clic sur une case permet de saisir.'
  },
  {
    cible: 'nav-/employes',
    titre: 'Les employés',
    texte: 'Comptes, contrats, plannings de présence, régularisations d’heures et absences.'
  },
  {
    cible: 'nav-/export',
    titre: 'L’export du comptable',
    texte: 'L’état préparatoire du mois, en Excel, à envoyer en fin de mois.'
  },
  {
    cible: 'nav-/parametres',
    titre: 'Les paramètres',
    texte: 'Motifs d’absence et de déplacement, jours de fermeture, seuils de présents, coefficient IK.'
  },
  {
    cible: 'nav-/guide',
    titre: 'Une question ?',
    texte: 'Le guide d’utilisation explique chaque action pas à pas.'
  },
  {
    cible: 'visite',
    titre: 'À revoir quand vous voulez',
    texte: 'Ce bouton relance la visite à tout moment.'
  }
]

const etapes = ref([])
const index = ref(-1)

const active = computed(() => index.value >= 0)
const etape = computed(() => etapes.value[index.value] || null)
const derniere = computed(() => index.value === etapes.value.length - 1)

export function useVisiteGuidee() {
  const demarrer = (admin) => {
    etapes.value = admin ? ETAPES_ADMIN : ETAPES_EMPLOYE
    index.value = 0
  }
  const suivant = () => {
    if (derniere.value) index.value = -1
    else index.value += 1
  }
  const precedent = () => {
    if (index.value > 0) index.value -= 1
  }
  const fermer = () => {
    index.value = -1
  }
  return { active, etape, index, total: computed(() => etapes.value.length), derniere, demarrer, suivant, precedent, fermer }
}
