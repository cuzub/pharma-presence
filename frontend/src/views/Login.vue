<template>
  <div class="d-flex justify-content-center align-items-center login-page">
    <form class="carte login-carte" @submit.prevent="connecter">
      <div class="text-center mb-4">
        <div class="login-logo"><i class="bi bi-capsule"></i></div>
        <h1 class="h4 mt-2 mb-0">Suivi de l'équipe</h1>
        <p class="text-muted small mb-0">Connectez-vous avec l'identifiant fourni par la pharmacie</p>
      </div>

      <div v-if="route.query.expiree" class="alert alert-info py-2 small">Votre session a expiré, veuillez vous reconnecter.</div>
      <div v-if="erreur" class="alert alert-danger py-2" role="alert">{{ erreur }}</div>

      <div class="mb-3">
        <label for="identifiant" class="form-label">Identifiant</label>
        <input id="identifiant" v-model.trim="identifiant" class="form-control" autocomplete="username" autocapitalize="none" required autofocus />
      </div>
      <div class="mb-4">
        <label for="mot-de-passe" class="form-label">Mot de passe</label>
        <input id="mot-de-passe" v-model="motDePasse" type="password" class="form-control" autocomplete="current-password" required />
      </div>
      <button type="submit" class="btn btn-primary w-100" :disabled="enCours">
        <span v-if="enCours" class="spinner-border spinner-border-sm me-1"></span>
        Se connecter
      </button>
      <p class="text-muted small text-center mt-3 mb-0">Mot de passe oublié ? Demandez-en un nouveau à Elise.</p>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { accueil } from '../router'
import { messageErreur } from '../services/api'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const identifiant = ref('')
const motDePasse = ref('')
const erreur = ref('')
const enCours = ref(false)

const connecter = async () => {
  erreur.value = ''
  enCours.value = true
  try {
    await auth.login(identifiant.value, motDePasse.value)
    const redirect = typeof route.query.redirect === 'string' && route.query.redirect.startsWith('/') ? route.query.redirect : null
    router.push(auth.doitChangerMdp ? '/mot-de-passe' : redirect || accueil(auth.utilisateur))
  } catch (error) {
    erreur.value = await messageErreur(error, 'Connexion impossible')
    motDePasse.value = ''
  } finally {
    enCours.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 80vh;
}

.login-carte {
  width: 100%;
  max-width: 380px;
  padding: 2rem;
}

.login-logo {
  font-size: 2.5rem;
  color: var(--pharma-vert);
}
</style>
