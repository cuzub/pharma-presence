<template>
  <Modal :ouvert="ouvert" :titre="deplacement?.id ? 'Modifier le déplacement' : 'Nouveau déplacement'" @fermer="$emit('fermer')">
    <form id="form-deplacement" @submit.prevent="enregistrer">
      <div v-if="erreur" class="alert alert-danger py-2" role="alert">{{ erreur }}</div>
      <div v-if="deplacement?.statut === 'refuse'" class="alert alert-warning py-2 small">
        Refusé : {{ deplacement.motif_refus }}. Après correction, il repassera en attente de validation.
      </div>

      <div class="mb-3">
        <label for="dep-date" class="form-label">Date</label>
        <input id="dep-date" v-model="form.date" type="date" class="form-control" required />
      </div>
      <div class="mb-3">
        <label for="dep-motif" class="form-label">Motif</label>
        <select id="dep-motif" ref="champMotif" v-model="choix" class="form-select" required>
          <option value="" disabled>Choisir…</option>
          <option v-for="m in motifsProposes" :key="m.id" :value="m.id">{{ m.libelle }} — {{ formatNombre(m.km) }} km</option>
          <option :value="AUTRE">Autre (distance libre)</option>
        </select>
        <p v-if="!referentiel.motifsDeplacement.length" class="form-text mb-0">
          Aucun motif enregistré : la pharmacienne peut en créer dans <em>Paramètres</em>.
        </p>
      </div>
      <div v-if="choix === AUTRE" class="mb-3">
        <label for="dep-precision" class="form-label">Précision</label>
        <input id="dep-precision" v-model="form.motif" class="form-control" maxlength="255" required placeholder="ex : Pharmacie de Chartres" />
      </div>
      <div class="mb-0">
        <label for="dep-km" class="form-label">Distance (km)</label>
        <input
          v-if="choix === AUTRE"
          id="dep-km"
          v-model="form.km"
          type="number"
          min="0.1"
          max="5000"
          step="0.1"
          class="form-control"
          required
        />
        <input v-else id="dep-km" :value="kmAffiches" class="form-control" readonly tabindex="-1" placeholder="Renseignée par le motif" />
      </div>
      <p v-if="employeId && !deplacement?.id" class="form-text mb-0 mt-2">Un déplacement saisi par la pharmacienne est validé directement.</p>
    </form>
    <template #footer>
      <button v-if="deplacement?.id" type="button" class="btn btn-outline-danger me-auto" :disabled="enCours" @click="supprimer">
        <i class="bi bi-trash"></i> Supprimer
      </button>
      <button type="button" class="btn btn-outline-secondary" @click="$emit('fermer')">Annuler</button>
      <button type="submit" form="form-deplacement" class="btn btn-primary" :disabled="enCours">Enregistrer</button>
    </template>
  </Modal>
</template>

<script setup>
import { computed, nextTick, reactive, ref, watch } from 'vue'
import api, { messageErreur } from '../services/api'
import { useReferentielStore } from '../stores/referentiel'
import { aujourdhuiIso, formatFr, formatNombre } from '../utils/dates'
import Modal from './Modal.vue'

const AUTRE = 'autre'

const props = defineProps({
  ouvert: { type: Boolean, default: false },
  deplacement: { type: Object, default: null },
  // Saisie par la pharmacienne pour un employé donné (sinon : l'employé connecté).
  employeId: { type: Number, default: null },
  date: { type: String, default: '' }
})
const emit = defineEmits(['fermer', 'enregistre'])

const referentiel = useReferentielStore()
const form = reactive({ date: '', motif: '', km: '' })
const choix = ref('')
const erreur = ref('')
const enCours = ref(false)
const champMotif = ref(null)

// Motifs actifs, plus celui du déplacement modifié s'il a été désactivé depuis.
const motifsProposes = computed(() =>
  referentiel.motifsDeplacement.filter((m) => m.actif || m.id === props.deplacement?.motif_deplacement_id))

const kmAffiches = computed(() => {
  if (choix.value === '') return ''
  // Motif inchangé : on affiche les km enregistrés à l'origine (l'historique ne bouge pas).
  if (props.deplacement?.id && choix.value === props.deplacement.motif_deplacement_id) return formatNombre(props.deplacement.km)
  const motif = referentiel.motifsDeplacement.find((m) => m.id === choix.value)
  return motif ? formatNombre(motif.km) : ''
})

watch(() => props.ouvert, async (ouvert) => {
  if (!ouvert) return
  erreur.value = ''
  const d = props.deplacement
  const autre = d?.id && !d.motif_deplacement_id
  Object.assign(form, {
    date: d?.date ?? (props.date || aujourdhuiIso()),
    motif: autre ? d.motif : '',
    km: autre ? d.km : ''
  })
  choix.value = d?.id ? (d.motif_deplacement_id ?? AUTRE) : ''
  try {
    await referentiel.chargerMotifsDeplacement(true)
  } catch (error) {
    erreur.value = await messageErreur(error)
  }
  await nextTick()
  champMotif.value?.focus()
}, { immediate: true })

const charge = () => {
  const autre = choix.value === AUTRE
  return {
    ...(props.employeId ? { employe_id: props.employeId } : {}),
    date: form.date,
    motif_deplacement_id: autre ? null : choix.value,
    motif: autre ? form.motif : null,
    km: autre ? form.km : null
  }
}

const executer = async (requete) => {
  erreur.value = ''
  enCours.value = true
  try {
    await requete()
    emit('enregistre')
  } catch (error) {
    erreur.value = await messageErreur(error)
  } finally {
    enCours.value = false
  }
}

const enregistrer = () => executer(() =>
  props.deplacement?.id ? api.put(`/deplacements/${props.deplacement.id}`, charge()) : api.post('/deplacements', charge()))

const supprimer = () => {
  if (confirm(`Supprimer le déplacement du ${formatFr(props.deplacement.date)} (${props.deplacement.motif}) ?`)) {
    executer(() => api.delete(`/deplacements/${props.deplacement.id}`))
  }
}
</script>
