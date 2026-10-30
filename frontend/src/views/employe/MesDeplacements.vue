<template>
  <div>
    <div class="page-titre">
      <h1 class="h4 mb-0">Mes déplacements professionnels</h1>
      <button type="button" class="btn btn-primary" @click="ouvrir(null)">
        <i class="bi bi-plus-lg"></i> Déclarer un déplacement
      </button>
    </div>

    <p class="text-muted small">
      Déclarez ici vos déplacements professionnels avec votre véhicule personnel. La pharmacienne les valide avant de les transmettre
      au comptable pour le calcul des indemnités kilométriques.
    </p>

    <div v-if="erreur" class="alert alert-danger">{{ erreur }}</div>

    <div class="carte p-0">
      <table class="table mb-0">
        <thead>
          <tr>
            <th>Date</th>
            <th>Trajet</th>
            <th>Motif</th>
            <th class="text-end">Km</th>
            <th>Statut</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="!deplacements.length">
            <td colspan="6" class="text-center text-muted py-4">Aucun déplacement déclaré.</td>
          </tr>
          <tr v-for="d in deplacements" :key="d.id">
            <td>{{ formatFr(d.date) }}</td>
            <td>{{ d.depart }} → {{ d.arrivee }}</td>
            <td class="small">{{ d.motif }}</td>
            <td class="text-end">{{ formatNombre(d.km) }}</td>
            <td>
              <span :class="['badge', STATUTS_DEPLACEMENT[d.statut].classe]">{{ STATUTS_DEPLACEMENT[d.statut].libelle }}</span>
              <div v-if="d.motif_refus" class="small text-danger">{{ d.motif_refus }}</div>
            </td>
            <td class="text-end text-nowrap">
              <template v-if="d.statut !== 'valide'">
                <button type="button" class="btn btn-sm btn-outline-secondary me-1" title="Modifier" @click="ouvrir(d)">
                  <i class="bi bi-pencil"></i>
                </button>
                <button type="button" class="btn btn-sm btn-outline-secondary" title="Supprimer" @click="supprimer(d)">
                  <i class="bi bi-trash"></i>
                </button>
              </template>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <DeplacementModal :ouvert="modalOuvert" :deplacement="deplacementEdite" @fermer="modalOuvert = false" @enregistre="apresEnregistrement" />
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import DeplacementModal from '../../components/DeplacementModal.vue'
import api, { messageErreur } from '../../services/api'
import { formatFr, formatNombre } from '../../utils/dates'
import { STATUTS_DEPLACEMENT } from '../../utils/statuts'

const deplacements = ref([])
const erreur = ref('')
const modalOuvert = ref(false)
const deplacementEdite = ref(null)

const charger = async () => {
  erreur.value = ''
  try {
    deplacements.value = (await api.get('/deplacements')).data
  } catch (error) {
    erreur.value = await messageErreur(error)
  }
}

const ouvrir = (d) => {
  deplacementEdite.value = d
  modalOuvert.value = true
}

const apresEnregistrement = () => {
  modalOuvert.value = false
  charger()
}

const supprimer = async (d) => {
  if (!confirm(`Supprimer le déplacement du ${formatFr(d.date)} ?`)) return
  try {
    await api.delete(`/deplacements/${d.id}`)
    await charger()
  } catch (error) {
    erreur.value = await messageErreur(error)
  }
}

onMounted(charger)
</script>
