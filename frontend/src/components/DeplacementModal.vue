<template>
  <Modal :ouvert="ouvert" :titre="deplacement?.id ? 'Modifier le déplacement' : 'Nouveau déplacement'" @fermer="$emit('fermer')">
    <form id="form-deplacement" @submit.prevent="enregistrer">
      <div v-if="erreur" class="alert alert-danger py-2" role="alert">{{ erreur }}</div>
      <div v-if="deplacement?.statut === 'refuse'" class="alert alert-warning py-2 small">
        Refusé : {{ deplacement.motif_refus }}. Après correction, il repassera en attente de validation.
      </div>

      <div v-if="choisirEmploye" class="mb-3">
        <label for="dep-employe" class="form-label">Employé</label>
        <select id="dep-employe" v-model="form.employe_id" class="form-select" required>
          <option :value="null" disabled>Choisir…</option>
          <option v-for="e in referentiel.employes" :key="e.id" :value="e.id">{{ e.nom }} {{ e.prenom }}</option>
        </select>
      </div>
      <div class="row g-3 mb-3">
        <div class="col-sm-6">
          <label for="dep-date" class="form-label">Date</label>
          <input id="dep-date" v-model="form.date" type="date" class="form-control" required />
        </div>
        <div class="col-sm-6">
          <label for="dep-km" class="form-label">Distance (km)</label>
          <input id="dep-km" v-model="form.km" type="number" min="0.1" max="5000" step="0.1" class="form-control" required />
        </div>
      </div>
      <div class="row g-3 mb-3">
        <div class="col-sm-6">
          <label for="dep-depart" class="form-label">Départ</label>
          <input id="dep-depart" v-model="form.depart" class="form-control" maxlength="120" required placeholder="ex : Pharmacie" />
        </div>
        <div class="col-sm-6">
          <label for="dep-arrivee" class="form-label">Arrivée</label>
          <input id="dep-arrivee" v-model="form.arrivee" class="form-control" maxlength="120" required placeholder="ex : Grossiste, EHPAD…" />
        </div>
      </div>
      <div>
        <label for="dep-motif" class="form-label">Motif</label>
        <input id="dep-motif" v-model="form.motif" class="form-control" maxlength="255" required placeholder="ex : Livraison patient, formation…" />
      </div>
      <p v-if="choisirEmploye && !deplacement?.id" class="form-text mb-0 mt-2">Un déplacement saisi par la pharmacienne est validé directement.</p>
    </form>
    <template #footer>
      <button type="button" class="btn btn-outline-secondary" @click="$emit('fermer')">Annuler</button>
      <button type="submit" form="form-deplacement" class="btn btn-primary" :disabled="enCours">Enregistrer</button>
    </template>
  </Modal>
</template>

<script setup>
import { reactive, ref, watch } from 'vue'
import api, { messageErreur } from '../services/api'
import { useReferentielStore } from '../stores/referentiel'
import { aujourdhuiIso } from '../utils/dates'
import Modal from './Modal.vue'

const props = defineProps({
  ouvert: { type: Boolean, default: false },
  deplacement: { type: Object, default: null },
  choisirEmploye: { type: Boolean, default: false }
})
const emit = defineEmits(['fermer', 'enregistre'])

const referentiel = useReferentielStore()
const form = reactive({ employe_id: null, date: '', depart: '', arrivee: '', motif: '', km: '' })
const erreur = ref('')
const enCours = ref(false)

watch(() => props.ouvert, async (ouvert) => {
  if (!ouvert) return
  erreur.value = ''
  const d = props.deplacement
  Object.assign(form, {
    employe_id: d?.employe_id ?? null,
    date: d?.date ?? aujourdhuiIso(),
    depart: d?.depart ?? '',
    arrivee: d?.arrivee ?? '',
    motif: d?.motif ?? '',
    km: d?.km ?? ''
  })
  if (props.choisirEmploye && !referentiel.employes.length) await referentiel.chargerEmployes()
}, { immediate: true })

const enregistrer = async () => {
  erreur.value = ''
  enCours.value = true
  try {
    if (props.deplacement?.id) {
      await api.put(`/deplacements/${props.deplacement.id}`, form)
    } else {
      await api.post('/deplacements', form)
    }
    emit('enregistre')
  } catch (error) {
    erreur.value = await messageErreur(error)
  } finally {
    enCours.value = false
  }
}
</script>
