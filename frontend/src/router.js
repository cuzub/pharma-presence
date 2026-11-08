import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from './stores/auth'

const routes = [
  { path: '/login', name: 'login', component: () => import('./views/Login.vue'), meta: { public: true } },
  { path: '/mot-de-passe', name: 'mot-de-passe', component: () => import('./views/ChangerMotDePasse.vue'), meta: { mdpProvisoireAutorise: true } },

  { path: '/', name: 'tableau', component: () => import('./views/admin/TableauMois.vue'), meta: { role: 'admin' } },
  { path: '/employes', name: 'employes', component: () => import('./views/admin/Employes.vue'), meta: { role: 'admin' } },
  { path: '/export', name: 'export', component: () => import('./views/admin/Export.vue'), meta: { role: 'admin' } },
  { path: '/historique', name: 'historique', component: () => import('./views/admin/Historique.vue'), meta: { role: 'admin' } },
  { path: '/parametres', name: 'parametres', component: () => import('./views/admin/Parametres.vue'), meta: { role: 'admin' } },
  { path: '/statistiques', name: 'statistiques', component: () => import('./views/admin/Statistiques.vue'), meta: { role: 'admin' } },

  { path: '/mon-mois', name: 'mon-mois', component: () => import('./views/employe/MonMois.vue'), meta: { role: 'employe' } },
  // Ancienne page : les déplacements se saisissent désormais dans le calendrier.
  { path: '/mes-deplacements', redirect: '/mon-mois' },

  { path: '/guide', name: 'guide', component: () => import('./views/Guide.vue') },

  { path: '/:pathMatch(.*)*', redirect: '/' }
]

export const accueil = (utilisateur) => (utilisateur?.role === 'admin' ? '/' : '/mon-mois')

export const garde = async (to) => {
  const auth = useAuthStore()
  if (!auth.sessionChargee) await auth.chargerSession()

  if (to.meta.public) {
    return auth.estConnecte ? accueil(auth.utilisateur) : true
  }
  if (!auth.estConnecte) {
    return { path: '/login', query: to.fullPath !== '/' ? { redirect: to.fullPath } : {} }
  }
  if (auth.doitChangerMdp && !to.meta.mdpProvisoireAutorise) {
    return '/mot-de-passe'
  }
  if (to.meta.role && to.meta.role !== auth.utilisateur.role) {
    return accueil(auth.utilisateur)
  }
  return true
}

const router = createRouter({ history: createWebHistory(import.meta.env.BASE_URL), routes })
router.beforeEach(garde)

export default router
