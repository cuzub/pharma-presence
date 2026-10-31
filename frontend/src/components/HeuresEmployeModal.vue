<template>
  <Modal :ouvert="!!employe" :titre="employe ? `Heures +/- — ${employe.prenom} ${employe.nom}` : ''" taille="lg" @fermer="$emit('fermer')">
    <template v-if="employe">
      <div v-if="erreur" class="alert alert-danger py-2 small" role="alert">{{ erreur }}</div>

      <form class="border rounded p-2 mb-3" data-form-regularisation @submit.prevent="enregistrer">
        <div v-if="editee" class="small fw-semibold mb-2">Modification du {{ formatFr(editee.jour) }}</div>

        <div class="d-flex flex-wrap align-items-center gap-2 mb-2">
          <div class="btn-group btn-group-sm" role="group" aria-label="Opération">
            <button
              type="button"
              :class="['btn', form.sens === 'credit' ? 'btn-success' : 'btn-outline-success']"
              :aria-pressed="form.sens === 'credit'"
              data-sens="credit"
              @click="form.sens = 'credit'"
            >
              <i class="bi bi-plus-circle"></i> Ajouter
            </button>
            <button
              type="button"
              :class="['btn', form.sens === 'debit' ? 'btn-warning' : 'btn-outline-warning']"
              :aria-pressed="form.sens === 'debit'"
              data-sens="debit"
              @click="form.sens = 'debit'"
            >
              <i class="bi bi-dash-circle"></i> Retirer
            </button>
          </div>
          <label for="hpm-heures" class="visually-hidden">Heures</label>
          <select id="hpm-heures" v-model.number="form.heures" class="form-select form-select-sm champ-heures">
            <option v-for="h in HEURES" :key="h" :value="h">{{ h }} h</option>
          </select>
          <label for="hpm-minutes" class="visually-hidden">Minutes</label>
          <select id="hpm-minutes" v-model.number="form.minutes" class="form-select form-select-sm champ-heures">
            <option v-for="m in MINUTES" :key="m" :value="m">{{ String(m).padStart(2, '0') }} min</option>
          </select>
          <label for="hpm-jour" class="visually-hidden">Date</label>
          <input id="hpm-jour" v-model="form.jour" type="date" class="form-control form-control-sm champ-date" required />
          <div class="small text-nowrap" data-apercu>
            <template v-if="minutes !== null">
              <span :class="classe(soldeAvant)">{{ libelle(soldeAvant) }}</span>
              <i class="bi bi-arrow-right mx-1"></i>
              <strong :class="classe(soldeApres)">{{ libelle(soldeApres) }}</strong>
            </template>
            <span v-else class="text-muted">Indiquez une durée.</span>
          </div>
        </div>

        <div class="d-flex flex-wrap align-items-center gap-2">
          <label for="hpm-commentaire" class="visually-hidden">Commentaire</label>
          <input id="hpm-commentaire" v-model.trim="form.commentaire" maxlength="200" class="form-control form-control-sm flex-grow-1" placeholder="Commentaire (facultatif)" />
          <button v-if="editee" type="button" class="btn btn-sm btn-outline-secondary" @click="reinitialiser">Annuler</button>
          <button type="submit" class="btn btn-sm btn-primary" :disabled="enCours || minutes === null">
            {{ editee ? 'Enregistrer la modification' : 'Enregistrer' }}
          </button>
        </div>
      </form>

      <h6 class="small fw-semibold mb-1">Historique des régularisations</h6>
      <div v-if="regularisations.length" class="historique">
      <table class="table table-sm align-middle mb-0">
        <thead>
          <tr>
            <th>Date</th>
            <th class="text-end">Heures</th>
            <th>Commentaire</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in regularisations" :key="r.id" :class="{ 'table-active': editee?.id === r.id }" data-regularisation>
            <td class="text-nowrap">{{ formatFr(r.jour) }}</td>
            <td class="text-end"><span class="badge regularisation">{{ formatMinutes(r.minutes) }}</span></td>
            <td class="w-100">{{ r.commentaire }}</td>
            <td class="text-nowrap text-end">
              <button type="button" class="btn btn-sm btn-outline-secondary" title="Modifier" :aria-label="`Modifier la régularisation du ${formatFr(r.jour)}`" @click="editer(r)">
                <i class="bi bi-pencil"></i>
              </button>
              <button type="button" class="btn btn-sm btn-outline-danger ms-1" title="Supprimer" :aria-label="`Supprimer la régularisation du ${formatFr(r.jour)}`" @click="supprimer(r)">
                <i class="bi bi-trash"></i>
              </button>
            </td>
          </tr>
        </tbody>
      </table>
      </div>
      <p v-else class="text-muted small mb-0">Aucune régularisation pour l'instant.</p>
    </template>
  </Modal>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import api, { messageErreur } from '../services/api'
import { aujourdhuiIso, formatFr, formatMinutes, minutesRegularisation } from '../utils/dates'
import Modal from './Modal.vue'

const HEURES = Array.from({ length: 13 }, (_, i) => i)
const MINUTES = [0, 15, 30, 45]

const props = defineProps({ employe: { type: Object, default: null } })
const emit = defineEmits(['fermer', 'modifie'])

const regularisations = ref([])
const solde = ref(0)
const erreur = ref('')
const enCours = ref(false)
const editee = ref(null)
const form = reactive({})

const reinitialiser = () => {
  editee.value = null
  Object.assign(form, { sens: 'credit', heures: 0, minutes: 0, jour: aujourdhuiIso(), commentaire: '' })
}
reinitialiser()

const minutes = computed(() => minutesRegularisation(form.sens, form.heures, form.minutes))
// En modification, l'ancienne valeur est retirée du solde avant d'appliquer la nouvelle.
const soldeAvant = computed(() => solde.value)
const soldeApres = computed(() => solde.value - (editee.value?.minutes || 0) + (minutes.value || 0))

const libelle = (m) => formatMinutes(m) || '0'
const classe = (m) => (m < 0 ? 'minutes-moins' : m > 0 ? 'minutes-plus' : '')

const charger = async () => {
  try {
    const donnees = (await api.get(`/employes/${props.employe.id}/regularisations`)).data
    regularisations.value = donnees.regularisations
    solde.value = donnees.solde_minutes
  } catch (error) {
    erreur.value = await messageErreur(error)
  }
}

watch(() => props.employe?.id, (id) => {
  erreur.value = ''
  regularisations.value = []
  solde.value = 0
  reinitialiser()
  if (id) charger()
}, { immediate: true })

const editer = (r) => {
  erreur.value = ''
  editee.value = r
  const total = Math.abs(r.minutes)
  Object.assign(form, {
    sens: r.minutes < 0 ? 'debit' : 'credit',
    heures: Math.floor(total / 60),
    minutes: total % 60,
    jour: r.jour,
    commentaire: r.commentaire || ''
  })
}

const enregistrer = async () => {
  erreur.value = ''
  if (minutes.value === null) {
    erreur.value = 'Indiquez une durée non nulle.'
    return
  }
  const donnees = { jour: form.jour, minutes: minutes.value, commentaire: form.commentaire }
  enCours.value = true
  try {
    if (editee.value) await api.put(`/regularisations/${editee.value.id}`, donnees)
    else await api.post(`/employes/${props.employe.id}/regularisations`, donnees)
    reinitialiser()
    await charger()
    emit('modifie')
  } catch (error) {
    erreur.value = await messageErreur(error)
  } finally {
    enCours.value = false
  }
}

const supprimer = async (r) => {
  if (!confirm(`Supprimer la régularisation de ${formatMinutes(r.minutes)} du ${formatFr(r.jour)} ?`)) return
  erreur.value = ''
  try {
    await api.delete(`/regularisations/${r.id}`)
    if (editee.value?.id === r.id) reinitialiser()
    await charger()
    emit('modifie')
  } catch (error) {
    erreur.value = await messageErreur(error)
  }
}
</script>

<style scoped>
.champ-heures {
  width: 5rem;
}

.champ-date {
  width: 9.5rem;
}

.historique {
  max-height: 11rem;
  overflow-y: auto;
}

.historique thead th {
  position: sticky;
  top: 0;
  background: var(--bs-body-bg);
}
</style>
