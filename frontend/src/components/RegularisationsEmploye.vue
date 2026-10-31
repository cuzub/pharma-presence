<template>
  <section class="mb-4" data-regularisations>
    <div class="d-flex flex-wrap align-items-baseline gap-2 mb-2">
      <h6 class="mb-0">Heures +/- : régularisations</h6>
      <span class="small text-muted">Solde à ce jour :</span>
      <span :class="['fw-semibold', solde < 0 ? 'minutes-moins' : 'minutes-plus']" data-solde-fiche>{{ formatMinutes(solde) || '0' }}</span>
    </div>
    <div v-if="erreur" class="alert alert-danger py-2 small" role="alert">{{ erreur }}</div>

    <form class="row g-2 align-items-end mb-2" @submit.prevent="enregistrer">
      <div class="col-sm-3">
        <label for="reg-sens" class="form-label small mb-1">Opération</label>
        <select id="reg-sens" v-model="form.sens" class="form-select form-select-sm">
          <option value="credit">Créditer (+)</option>
          <option value="debit">Débiter (−)</option>
        </select>
      </div>
      <div class="col-4 col-sm-2">
        <label for="reg-heures" class="form-label small mb-1">Heures</label>
        <input id="reg-heures" v-model="form.heures" type="number" min="0" max="500" step="1" class="form-control form-control-sm" />
      </div>
      <div class="col-4 col-sm-2">
        <label for="reg-minutes" class="form-label small mb-1">Minutes</label>
        <input id="reg-minutes" v-model="form.minutes" type="number" min="0" max="55" step="5" class="form-control form-control-sm" />
      </div>
      <div class="col-4 col-sm-3">
        <label for="reg-jour" class="form-label small mb-1">Date</label>
        <input id="reg-jour" v-model="form.jour" type="date" class="form-control form-control-sm" required />
      </div>
      <div class="col-sm-2 d-flex gap-1">
        <button type="submit" class="btn btn-sm btn-primary flex-grow-1" :disabled="enCours">{{ editee ? 'Modifier' : 'Ajouter' }}</button>
        <button v-if="editee" type="button" class="btn btn-sm btn-outline-secondary" title="Annuler" @click="reinitialiser">
          <i class="bi bi-x-lg"></i>
        </button>
      </div>
      <div class="col-12">
        <label for="reg-commentaire" class="visually-hidden">Commentaire</label>
        <input
          id="reg-commentaire"
          v-model.trim="form.commentaire"
          maxlength="200"
          class="form-control form-control-sm"
          placeholder="Commentaire (facultatif) : heures payées, récupération, solde de départ…"
        />
      </div>
    </form>

    <ul v-if="regularisations.length" class="list-group list-group-flush small">
      <li v-for="r in regularisations" :key="r.id" class="list-group-item d-flex align-items-center gap-2 px-0 py-1" data-regularisation>
        <span class="text-muted text-nowrap">{{ formatFr(r.jour) }}</span>
        <span class="badge regularisation">{{ formatMinutes(r.minutes) }}</span>
        <span class="flex-grow-1 text-truncate">{{ r.commentaire }}</span>
        <button type="button" class="btn btn-sm btn-outline-secondary" title="Modifier" :aria-label="`Modifier la régularisation du ${formatFr(r.jour)}`" @click="editer(r)">
          <i class="bi bi-pencil"></i>
        </button>
        <button type="button" class="btn btn-sm btn-outline-danger" title="Supprimer" :aria-label="`Supprimer la régularisation du ${formatFr(r.jour)}`" @click="supprimer(r)">
          <i class="bi bi-trash"></i>
        </button>
      </li>
    </ul>
    <p v-else class="text-muted small mb-0">Aucune régularisation.</p>
    <p class="form-text mb-0">
      Crédit ou débit du compteur (heures payées, récupération, solde de départ, correction). Visible dans le tableau du mois et le
      calendrier de l'employé, et compté dans le solde et les statistiques.
    </p>
  </section>
</template>

<script setup>
import { reactive, ref, watch } from 'vue'
import api, { messageErreur } from '../services/api'
import { aujourdhuiIso, formatFr, formatMinutes, minutesRegularisation } from '../utils/dates'

const props = defineProps({ employeId: { type: Number, required: true } })
const emit = defineEmits(['modifie'])

const regularisations = ref([])
const solde = ref(0)
const erreur = ref('')
const enCours = ref(false)
const editee = ref(null)
const form = reactive({ sens: 'credit', heures: '', minutes: '', jour: aujourdhuiIso(), commentaire: '' })

const reinitialiser = () => {
  editee.value = null
  Object.assign(form, { sens: 'credit', heures: '', minutes: '', jour: aujourdhuiIso(), commentaire: '' })
}

const charger = async () => {
  try {
    const donnees = (await api.get(`/employes/${props.employeId}/regularisations`)).data
    regularisations.value = donnees.regularisations
    solde.value = donnees.solde_minutes
  } catch (error) {
    erreur.value = await messageErreur(error)
  }
}

watch(() => props.employeId, () => {
  erreur.value = ''
  reinitialiser()
  charger()
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
  const minutes = minutesRegularisation(form.sens, form.heures, form.minutes)
  if (minutes === null) {
    erreur.value = 'Indiquez une durée non nulle (heures entières, minutes de 0 à 55).'
    return
  }
  const donnees = { jour: form.jour, minutes, commentaire: form.commentaire }
  enCours.value = true
  try {
    if (editee.value) await api.put(`/regularisations/${editee.value.id}`, donnees)
    else await api.post(`/employes/${props.employeId}/regularisations`, donnees)
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
