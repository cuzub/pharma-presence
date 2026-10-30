<template>
  <nav class="navbar navbar-expand-lg navbar-dark app-navbar">
    <div class="container-fluid px-3 px-lg-4">
      <RouterLink class="navbar-brand d-flex align-items-center gap-2" :to="auth.estAdmin ? '/' : '/mon-mois'">
        <i class="bi bi-capsule"></i> Présences
      </RouterLink>
      <ul class="navbar-nav me-auto flex-row flex-wrap gap-1">
        <li v-for="lien in liens" :key="lien.to" class="nav-item">
          <RouterLink class="nav-link px-2" :to="lien.to" active-class="active" :exact-active-class="lien.to === '/' ? 'active' : ''">
            <i :class="['bi', lien.icone]"></i> {{ lien.libelle }}
            <span v-if="lien.badge" class="badge rounded-pill text-bg-warning ms-1">{{ lien.badge }}</span>
          </RouterLink>
        </li>
      </ul>
      <div class="d-flex align-items-center gap-2 text-white">
        <RouterLink to="/mot-de-passe" class="nav-link text-white-50 small" title="Changer mon mot de passe">
          <i class="bi bi-person-circle"></i> {{ auth.nomAffiche }}
        </RouterLink>
        <button type="button" class="btn btn-sm btn-outline-light" @click="deconnecter">
          <i class="bi bi-box-arrow-right"></i> Déconnexion
        </button>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useReferentielStore } from '../stores/referentiel'

const auth = useAuthStore()
const referentiel = useReferentielStore()
const router = useRouter()
const route = useRoute()

const liens = computed(() => auth.estAdmin
  ? [
      { to: '/', libelle: 'Tableau du mois', icone: 'bi-grid-3x3' },
      { to: '/calendrier', libelle: 'Calendrier', icone: 'bi-calendar3' },
      { to: '/absences', libelle: 'Absences', icone: 'bi-calendar-x' },
      { to: '/deplacements', libelle: 'Déplacements', icone: 'bi-car-front', badge: referentiel.deplacementsEnAttente || null },
      { to: '/employes', libelle: 'Employés', icone: 'bi-people' },
      { to: '/export', libelle: 'Export comptable', icone: 'bi-file-earmark-spreadsheet' },
      { to: '/parametres', libelle: 'Paramètres', icone: 'bi-gear' }
    ]
  : [
      { to: '/mon-mois', libelle: 'Mon mois', icone: 'bi-calendar3' },
      { to: '/mes-deplacements', libelle: 'Mes déplacements', icone: 'bi-car-front' }
    ])

// Recompté à chaque changement de page (un employé a pu déclarer un déplacement entre-temps).
watch(() => route.path, () => {
  if (auth.estAdmin) referentiel.compterDeplacementsEnAttente().catch(() => {})
}, { immediate: true })

const deconnecter = async () => {
  await auth.logout()
  referentiel.reinitialiser()
  router.push('/login')
}
</script>
