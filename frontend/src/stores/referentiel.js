import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import api from '../services/api'

// Données de référence partagées entre les écrans (motifs d'absence, liste des employés).
export const useReferentielStore = defineStore('referentiel', () => {
  const motifs = ref([])
  const employes = ref([])
  const deplacementsEnAttente = ref(0)

  const motifsActifs = computed(() => motifs.value.filter((m) => m.actif))

  const chargerMotifs = async (forcer = false) => {
    if (motifs.value.length && !forcer) return motifs.value
    motifs.value = (await api.get('/motifs')).data
    return motifs.value
  }

  const chargerEmployes = async (statut = 'tous') => {
    employes.value = (await api.get('/employes', { params: { statut } })).data
    return employes.value
  }

  const compterDeplacementsEnAttente = async () => {
    deplacementsEnAttente.value = (await api.get('/deplacements', { params: { statut: 'en_attente' } })).data.length
    return deplacementsEnAttente.value
  }

  const reinitialiser = () => {
    motifs.value = []
    employes.value = []
    deplacementsEnAttente.value = 0
  }

  return {
    motifs,
    motifsActifs,
    employes,
    deplacementsEnAttente,
    chargerMotifs,
    chargerEmployes,
    compterDeplacementsEnAttente,
    reinitialiser
  }
})
