import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import api from '../services/api'

// Données de référence partagées entre les écrans (motifs d'absence et de déplacement, liste des employés).
export const useReferentielStore = defineStore('referentiel', () => {
  const motifs = ref([])
  const motifsDeplacement = ref([])
  const employes = ref([])

  const motifsActifs = computed(() => motifs.value.filter((m) => m.actif))

  const chargerMotifs = async (forcer = false) => {
    if (motifs.value.length && !forcer) return motifs.value
    motifs.value = (await api.get('/motifs')).data
    return motifs.value
  }

  const chargerMotifsDeplacement = async (forcer = false) => {
    if (motifsDeplacement.value.length && !forcer) return motifsDeplacement.value
    motifsDeplacement.value = (await api.get('/deplacements/motifs')).data
    return motifsDeplacement.value
  }

  const chargerEmployes = async (statut = 'tous') => {
    employes.value = (await api.get('/employes', { params: { statut } })).data
    return employes.value
  }

  const reinitialiser = () => {
    motifs.value = []
    motifsDeplacement.value = []
    employes.value = []
  }

  return {
    motifs,
    motifsActifs,
    motifsDeplacement,
    employes,
    chargerMotifs,
    chargerMotifsDeplacement,
    chargerEmployes,
    reinitialiser
  }
})
