<template>
  <div class="app-shell" :class="{ 'avec-barre': barreVisible, 'barre-reduite': reduite }">
    <AppHeader v-if="barreVisible" />
    <main class="container-fluid py-3 px-3 px-lg-4">
      <RouterView />
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import AppHeader from './components/AppHeader.vue'
import { useAuthStore } from './stores/auth'
import { useBarreLaterale } from './composables/useBarreLaterale'

const auth = useAuthStore()
const { reduite } = useBarreLaterale()
const barreVisible = computed(() => auth.estConnecte && !auth.doitChangerMdp)
</script>
