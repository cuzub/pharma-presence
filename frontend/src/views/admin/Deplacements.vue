<template>
  <div>
    <div class="page-titre">
      <h1 class="h4 mb-0">Déplacements professionnels</h1>
      <button type="button" class="btn btn-primary" @click="ouvrir(null)">
        <i class="bi bi-plus-lg"></i> Saisir un déplacement
      </button>
    </div>

    <ul class="nav nav-tabs mb-3">
      <li class="nav-item">
        <button type="button" :class="['nav-link', { active: onglet === 'en_attente' }]" @click="onglet = 'en_attente'">
          À valider <span v-if="nbEnAttente" class="badge text-bg-warning">{{ nbEnAttente }}</span>
        </button>
      </li>
      <li class="nav-item">
        <button type="button" :class="['nav-link', { active: onglet === 'mois' }]" @click="onglet = 'mois'">Par mois</button>
      </li>
    </ul>

    <div v-if="onglet === 'mois'" class="mb-3">
      <MoisNavigateur v-model="mois" />
    </div>

    <div v-if="erreur" class="alert alert-danger">{{ erreur }}</div>

    <div class="carte p-0">
      <table class="table table-hover mb-0">
        <thead>
          <tr>
            <th>Employé</th>
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
            <td colspan="7" class="text-center text-muted py-4">
              {{ onglet === 'en_attente' ? 'Aucun déplacement en attente de validation.' : 'Aucun déplacement ce mois-ci.' }}
            </td>
          </tr>
          <tr v-for="d in deplacements" :key="d.id">
            <td>{{ d.employe_nom }} {{ d.employe_prenom }}</td>
            <td>{{ formatFr(d.date) }}</td>
            <td>{{ d.depart }} → {{ d.arrivee }}</td>
            <td class="small">{{ d.motif }}</td>
            <td class="text-end">{{ formatNombre(d.km) }}</td>
            <td>
              <span :class="['badge', STATUTS_DEPLACEMENT[d.statut].classe]">{{ STATUTS_DEPLACEMENT[d.statut].libelle }}</span>
              <div v-if="d.motif_refus" class="small text-muted">{{ d.motif_refus }}</div>
            </td>
            <td class="text-end text-nowrap">
              <button v-if="d.statut !== 'valide'" type="button" class="btn btn-sm btn-success me-1" title="Valider" @click="valider(d)">
                <i class="bi bi-check-lg"></i> Valider
              </button>
              <button v-if="d.statut === 'en_attente'" type="button" class="btn btn-sm btn-outline-danger me-1" title="Refuser" @click="ouvrirRefus(d)">
                <i class="bi bi-x-lg"></i>
              </button>
              <button type="button" class="btn btn-sm btn-outline-secondary me-1" title="Modifier" @click="ouvrir(d)">
                <i class="bi bi-pencil"></i>
              </button>
              <button type="button" class="btn btn-sm btn-outline-secondary" title="Supprimer" @click="supprimer(d)">
                <i class="bi bi-trash"></i>
              </button>
            </td>
          </tr>
        </tbody>
        <tfoot v-if="onglet === 'mois' && totalValide">
          <tr>
            <th colspan="4" class="text-end">Total validé</th>
            <th class="text-end">{{ formatNombre(totalValide) }}</th>
            <th colspan="2"></th>
          </tr>
        </tfoot>
      </table>
    </div>

    <DeplacementModal :ouvert="modalOuvert" :deplacement="deplacementEdite" choisir-employe @fermer="modalOuvert = false" @enregistre="apresEnregistrement" />

    <Modal :ouvert="!!refus" titre="Refuser le déplacement" @fermer="refus = null">
      <form id="form-refus" @submit.prevent="refuser">
        <label for="motif-refus" class="form-label">Motif du refus (visible par l'employé)</label>
        <input id="motif-refus" v-model="motifRefus" class="form-control" maxlength="255" required />
      </form>
      <template #footer>
        <button type="button" class="btn btn-outline-secondary" @click="refus = null">Annuler</button>
        <button type="submit" form="form-refus" class="btn btn-danger">Refuser</button>
      </template>
    </Modal>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import DeplacementModal from '../../components/DeplacementModal.vue'
import Modal from '../../components/Modal.vue'
import MoisNavigateur from '../../components/MoisNavigateur.vue'
import { useMoisUrl } from '../../composables/useMoisUrl'
import api, { messageErreur } from '../../services/api'
import { useReferentielStore } from '../../stores/referentiel'
import { formatFr, formatNombre } from '../../utils/dates'
import { STATUTS_DEPLACEMENT } from '../../utils/statuts'

const referentiel = useReferentielStore()
const mois = useMoisUrl()
const onglet = ref('en_attente')
const deplacements = ref([])
const nbEnAttente = computed(() => referentiel.deplacementsEnAttente)
const erreur = ref('')
const modalOuvert = ref(false)
const deplacementEdite = ref(null)
const refus = ref(null)
const motifRefus = ref('')

const totalValide = computed(() =>
  deplacements.value.filter((d) => d.statut === 'valide').reduce((total, d) => total + d.km, 0))

const charger = async () => {
  erreur.value = ''
  try {
    const [liste] = await Promise.all([
      api.get('/deplacements', { params: onglet.value === 'en_attente' ? { statut: 'en_attente' } : { mois: mois.value } }),
      referentiel.compterDeplacementsEnAttente()
    ])
    deplacements.value = liste.data
  } catch (error) {
    erreur.value = await messageErreur(error)
  }
}

const action = async (promesse) => {
  try {
    await promesse
    await charger()
  } catch (error) {
    erreur.value = await messageErreur(error)
  }
}

const valider = (d) => action(api.post(`/deplacements/${d.id}/valider`))

const ouvrirRefus = (d) => {
  refus.value = d
  motifRefus.value = ''
}

const refuser = async () => {
  const d = refus.value
  refus.value = null
  await action(api.post(`/deplacements/${d.id}/refuser`, { motif_refus: motifRefus.value }))
}

const supprimer = (d) => {
  if (confirm(`Supprimer le déplacement du ${formatFr(d.date)} (${d.employe_prenom} ${d.employe_nom}) ?`)) {
    action(api.delete(`/deplacements/${d.id}`))
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

watch([onglet, mois], charger, { immediate: true })
</script>
