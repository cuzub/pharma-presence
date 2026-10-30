<template>
  <div class="app-shell">
    <AppHeader v-if="auth.estConnecte && !auth.doitChangerMdp" />
    <main class="container-fluid py-3 px-3 px-lg-4">
      <RouterView />
    </main>
  </div>
</template>

<script setup>
import AppHeader from './components/AppHeader.vue'
import { useAuthStore } from './stores/auth'

const auth = useAuthStore()
</script>
