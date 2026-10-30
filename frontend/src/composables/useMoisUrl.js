import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { estMoisValide, moisCourant } from '../utils/dates'

// Mois affiché, conservé dans l'URL (?mois=AAAA-MM) pour pouvoir recharger ou partager la page.
export const useMoisUrl = () => {
  const route = useRoute()
  const router = useRouter()
  return computed({
    get: () => (estMoisValide(route.query.mois) ? route.query.mois : moisCourant()),
    set: (mois) => router.replace({ query: { ...route.query, mois } })
  })
}
