<template>
  <div class="d-flex justify-content-center">
    <form class="carte mdp-carte" @submit.prevent="enregistrer">
      <h1 class="h4">{{ auth.doitChangerMdp ? 'Choisissez votre mot de passe' : 'Changer mon mot de passe' }}</h1>
      <p v-if="auth.doitChangerMdp" class="alert alert-info small">
        Vous utilisez un mot de passe provisoire. Pour protéger vos informations, choisissez un mot de passe personnel
        que vous seul(e) connaissez.
      </p>

      <div v-if="erreur" class="alert alert-danger py-2" role="alert">{{ erreur }}</div>
      <div v-if="succes" class="alert alert-success py-2" role="status">Mot de passe modifié.</div>

      <input type="text" :value="auth.utilisateur?.identifiant" autocomplete="username" hidden readonly />
      <div class="mb-3">
        <label for="actuel" class="form-label">Mot de passe actuel{{ auth.doitChangerMdp ? ' (provisoire)' : '' }}</label>
        <input id="actuel" v-model="actuel" type="password" class="form-control" autocomplete="current-password" required />
      </div>
      <div class="mb-3">
        <label for="nouveau" class="form-label">Nouveau mot de passe</label>
        <input id="nouveau" v-model="nouveau" type="password" class="form-control" autocomplete="new-password" :minlength="LONGUEUR_MIN_MDP" required />
        <div class="form-text">Au moins {{ LONGUEUR_MIN_MDP }} caractères. Une phrase facile à retenir fonctionne très bien.</div>
      </div>
      <div class="mb-4">
        <label for="confirmation" class="form-label">Confirmer le nouveau mot de passe</label>
        <input id="confirmation" v-model="confirmation" type="password" class="form-control" autocomplete="new-password" required />
      </div>
      <div class="d-flex gap-2">
        <button type="submit" class="btn btn-primary" :disabled="enCours">Enregistrer</button>
        <button v-if="auth.doitChangerMdp" type="button" class="btn btn-outline-secondary" @click="deconnecter">Se déconnecter</button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { accueil } from '../router'
import { messageErreur } from '../services/api'
import { useAuthStore } from '../stores/auth'
import { LONGUEUR_MIN_MDP } from '../utils/motDePasse'

const auth = useAuthStore()
const router = useRouter()
const actuel = ref('')
const nouveau = ref('')
const confirmation = ref('')
const erreur = ref('')
const succes = ref(false)
const enCours = ref(false)

const enregistrer = async () => {
  erreur.value = ''
  succes.value = false
  if (nouveau.value !== confirmation.value) {
    erreur.value = 'Les deux nouveaux mots de passe ne correspondent pas'
    return
  }
  const etaitProvisoire = auth.doitChangerMdp
  enCours.value = true
  try {
    await auth.changerMotDePasse(actuel.value, nouveau.value)
    actuel.value = nouveau.value = confirmation.value = ''
    if (etaitProvisoire) {
      router.push(accueil(auth.utilisateur))
    } else {
      succes.value = true
    }
  } catch (error) {
    erreur.value = await messageErreur(error)
  } finally {
    enCours.value = false
  }
}

const deconnecter = async () => {
  await auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.mdp-carte {
  width: 100%;
  max-width: 460px;
  padding: 2rem;
}
</style>
