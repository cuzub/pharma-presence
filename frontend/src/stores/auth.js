import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import api from '../services/api'

export const useAuthStore = defineStore('auth', () => {
  const utilisateur = ref(null)
  const sessionChargee = ref(false)

  const estConnecte = computed(() => !!utilisateur.value)
  const estAdmin = computed(() => utilisateur.value?.role === 'admin')
  const doitChangerMdp = computed(() => !!utilisateur.value?.doit_changer_mdp)
  const nomAffiche = computed(() => {
    const u = utilisateur.value
    if (!u) return ''
    return u.prenom ? `${u.prenom} ${u.nom}` : (u.nom_affiche || u.identifiant)
  })

  const chargerSession = async () => {
    try {
      utilisateur.value = (await api.get('/auth/me')).data
    } catch {
      utilisateur.value = null
    } finally {
      sessionChargee.value = true
    }
  }

  const login = async (identifiant, motDePasse) => {
    utilisateur.value = (await api.post('/auth/login', { identifiant, mot_de_passe: motDePasse })).data
    sessionChargee.value = true
  }

  const logout = async () => {
    try {
      await api.post('/auth/logout')
    } finally {
      utilisateur.value = null
    }
  }

  const changerMotDePasse = async (actuel, nouveau) => {
    utilisateur.value = (await api.post('/auth/mot-de-passe', {
      mot_de_passe_actuel: actuel,
      nouveau_mot_de_passe: nouveau
    })).data
  }

  const oublierSession = () => {
    utilisateur.value = null
  }

  const marquerChangementMdpRequis = () => {
    if (utilisateur.value) utilisateur.value = { ...utilisateur.value, doit_changer_mdp: true }
  }

  return {
    utilisateur,
    sessionChargee,
    estConnecte,
    estAdmin,
    doitChangerMdp,
    nomAffiche,
    chargerSession,
    login,
    logout,
    changerMotDePasse,
    oublierSession,
    marquerChangementMdpRequis
  }
})
