<template>
  <div>
    <div class="page-titre">
      <h1 class="h4 mb-0">Déplacements professionnels</h1>
      <MoisNavigateur v-model="mois" />
    </div>
    <p class="text-muted small">
      Déplacements déclarés par les employés (ou par vous). Pour en ajouter un, cliquez sur la date dans le
      <RouterLink to="/calendrier">calendrier</RouterLink> de l'employé.
    </p>

    <div v-if="erreur" class="alert alert-danger">{{ erreur }}</div>

    <div class="carte p-0">
      <table class="table table-hover mb-0">
        <thead>
          <tr>
            <th>Employé</th>
            <th>Date</th>
            <th>Motif</th>
            <th class="text-end">Km</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="!deplacements.length">
            <td colspan="5" class="text-center text-muted py-4">Aucun déplacement ce mois-ci.</td>
          </tr>
          <tr v-for="d in deplacements" :key="d.id">
            <td>{{ d.employe_nom }} {{ d.employe_prenom }}</td>
            <td>{{ formatFr(d.date) }}</td>
            <td>{{ d.motif }}</td>
            <td class="text-end">{{ formatNombre(d.km) }}</td>
            <td class="text-end text-nowrap">
              <button type="button" class="btn btn-sm btn-outline-secondary me-1" title="Modifier" :aria-label="`Modifier le déplacement ${d.motif}`" @click="ouvrir(d)">
                <i class="bi bi-pencil"></i>
              </button>
              <button type="button" class="btn btn-sm btn-outline-secondary" title="Supprimer" :aria-label="`Supprimer le déplacement ${d.motif}`" @click="supprimer(d)">
                <i class="bi bi-trash"></i>
              </button>
            </td>
          </tr>
        </tbody>
        <tfoot v-if="deplacements.length">
          <tr>
            <th colspan="3" class="text-end">Total</th>
            <th class="text-end">{{ formatNombre(total) }}</th>
            <th></th>
          </tr>
        </tfoot>
      </table>
    </div>

    <DeplacementModal :ouvert="modalOuvert" :deplacement="deplacementEdite" @fermer="modalOuvert = false" @enregistre="apresEnregistrement" />
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import DeplacementModal from '../../components/DeplacementModal.vue'
import MoisNavigateur from '../../components/MoisNavigateur.vue'
import { useMoisUrl } from '../../composables/useMoisUrl'
import api, { messageErreur } from '../../services/api'
import { formatFr, formatNombre } from '../../utils/dates'

const mois = useMoisUrl()
const deplacements = ref([])
const erreur = ref('')
const modalOuvert = ref(false)
const deplacementEdite = ref(null)

const total = computed(() => deplacements.value.reduce((somme, d) => somme + d.km, 0))

const charger = async () => {
  erreur.value = ''
  try {
    deplacements.value = (await api.get('/deplacements', { params: { mois: mois.value } })).data
  } catch (error) {
    erreur.value = await messageErreur(error)
  }
}

const supprimer = async (d) => {
  if (!confirm(`Supprimer le déplacement du ${formatFr(d.date)} (${d.employe_prenom} ${d.employe_nom}, ${d.motif}) ?`)) return
  try {
    await api.delete(`/deplacements/${d.id}`)
    await charger()
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

watch(mois, charger, { immediate: true })
</script>
