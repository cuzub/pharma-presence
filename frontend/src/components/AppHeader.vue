<template>
  <aside class="app-sidebar" :class="{ 'app-sidebar--reduite': reduite }">
    <div class="app-sidebar-entete">
      <button
        type="button"
        class="app-sidebar-bascule"
        :aria-expanded="!reduite"
        :title="reduite ? 'Afficher le menu' : 'Réduire le menu'"
        @click="basculer"
      >
        <svg viewBox="0 0 24 24" width="1.5rem" height="1.5rem" aria-hidden="true">
          <g transform="rotate(-45 12 12)">
            <path d="M12 8H7A4 4 0 0 0 3 12A4 4 0 0 0 7 16H12Z" :class="['capsule-moitie', { 'capsule-moitie--pleine': !reduite }]" />
            <path d="M12 8H17A4 4 0 0 1 17 16H12Z" :class="['capsule-moitie', { 'capsule-moitie--pleine': reduite }]" />
          </g>
        </svg>
      </button>
      <RouterLink class="app-sidebar-marque" :to="auth.estAdmin ? '/' : '/mon-mois'" title="Suivi">
        <span class="app-sidebar-texte">Suivi</span>
      </RouterLink>
    </div>
    <ul class="nav flex-column app-sidebar-liens">
      <li v-for="lien in liens" :key="lien.to" class="nav-item">
        <RouterLink class="nav-link" :to="lien.to" active-class="active" :exact-active-class="lien.to === '/' ? 'active' : ''" :title="lien.libelle">
          <i :class="['bi', lien.icone]"></i>
          <span class="app-sidebar-texte">{{ lien.libelle }}</span>
        </RouterLink>
      </li>
    </ul>
    <div class="app-sidebar-pied">
      <RouterLink to="/mot-de-passe" class="nav-link" title="Changer mon mot de passe">
        <i class="bi bi-person-circle"></i>
        <span class="app-sidebar-texte app-sidebar-nom" v-infobulle="auth.nomAffiche">{{ auth.nomAffiche }}</span>
      </RouterLink>
      <button type="button" class="btn btn-sm btn-outline-light app-sidebar-deconnexion" title="Déconnexion" @click="deconnecter">
        <i class="bi bi-box-arrow-right"></i>
        <span class="app-sidebar-texte">Déconnexion</span>
      </button>
    </div>
  </aside>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useReferentielStore } from '../stores/referentiel'
import { useBarreLaterale } from '../composables/useBarreLaterale'

const auth = useAuthStore()
const referentiel = useReferentielStore()
const router = useRouter()
const { reduite, basculer } = useBarreLaterale()

const liens = computed(() => auth.estAdmin
  ? [
      { to: '/', libelle: 'Tableau', icone: 'bi-grid-3x3' },
      { to: '/employes', libelle: 'Employés', icone: 'bi-people' },
      { to: '/export', libelle: 'Export', icone: 'bi-file-earmark-spreadsheet' },
      { to: '/historique', libelle: 'Historique', icone: 'bi-clock-history' },
      { to: '/statistiques', libelle: 'Statistiques', icone: 'bi-bar-chart' },
      { to: '/parametres', libelle: 'Paramètres', icone: 'bi-gear' },
      { to: '/guide', libelle: "Guide d'utilisation", icone: 'bi-book' }
    ]
  : [
      { to: '/mon-mois', libelle: 'Mon mois', icone: 'bi-calendar3' },
      { to: '/guide', libelle: "Guide d'utilisation", icone: 'bi-book' }
    ])

const deconnecter = async () => {
  await auth.logout()
  referentiel.reinitialiser()
  router.push('/login')
}
</script>
