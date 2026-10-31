import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { anneeCourante } from '../utils/dates'

const estAnneeValide = (annee) => /^\d{4}$/.test(annee || '') && Number(annee) >= 2000 && Number(annee) <= 2100

// Année affichée, conservée dans l'URL (?annee=AAAA) pour pouvoir recharger ou partager la page.
export const useAnneeUrl = () => {
  const route = useRoute()
  const router = useRouter()
  return computed({
    get: () => (estAnneeValide(route.query.annee) ? Number(route.query.annee) : anneeCourante()),
    set: (annee) => router.replace({ query: { ...route.query, annee: String(annee) } })
  })
}
