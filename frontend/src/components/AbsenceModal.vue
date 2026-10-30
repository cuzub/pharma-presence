<template>
  <Modal :ouvert="ouvert" :titre="absence?.id ? 'Modifier l’absence' : 'Nouvelle absence'" @fermer="$emit('fermer')">
    <form id="form-absence" @submit.prevent="enregistrer">
      <div v-if="erreur" class="alert alert-danger py-2" role="alert">{{ erreur }}</div>

      <div class="mb-3">
        <label for="absence-employe" class="form-label">Employé</label>
        <select id="absence-employe" v-model="form.employe_id" class="form-select" :disabled="!!employeFixe" required>
          <option :value="null" disabled>Choisir…</option>
          <option v-for="e in referentiel.employes" :key="e.id" :value="e.id">{{ e.nom }} {{ e.prenom }}</option>
        </select>
      </div>
      <div class="mb-3">
        <label for="absence-motif" class="form-label">Motif</label>
        <select id="absence-motif" v-model="form.motif_id" class="form-select" required>
          <option :value="null" disabled>Choisir…</option>
          <option v-for="m in motifsProposes" :key="m.id" :value="m.id">{{ m.libelle }}</option>
        </select>
      </div>
      <div class="row g-3 mb-3">
        <div class="col-sm-6">
          <label for="absence-debut" class="form-label">Premier jour d'absence</label>
          <input id="absence-debut" v-model="form.date_debut" type="date" class="form-control" required />
        </div>
        <div class="col-sm-6">
          <label for="absence-reprise" class="form-label">Jour de reprise</label>
          <input id="absence-reprise" v-model="form.date_reprise" type="date" class="form-control" :min="form.date_debut ? ajouterJours(form.date_debut, 1) : undefined" />
        </div>
      </div>
      <p class="form-text mt-n2">
        Le jour de reprise est le premier jour où l'employé revient travailler. Laissez-le vide s'il n'est pas encore connu
        (absence « en cours »).
      </p>
      <div>
        <label for="absence-commentaire" class="form-label">Commentaire <span class="text-muted">(facultatif)</span></label>
        <input id="absence-commentaire" v-model="form.commentaire" class="form-control" maxlength="255" />
      </div>
    </form>
    <template #footer>
      <button v-if="absence?.id" type="button" class="btn btn-outline-danger me-auto" :disabled="enCours" @click="supprimer">
        <i class="bi bi-trash"></i> Supprimer
      </button>
      <button type="button" class="btn btn-outline-secondary" @click="$emit('fermer')">Annuler</button>
      <button type="submit" form="form-absence" class="btn btn-primary" :disabled="enCours">Enregistrer</button>
    </template>
  </Modal>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import api, { messageErreur } from '../services/api'
import { useReferentielStore } from '../stores/referentiel'
import { ajouterJours } from '../utils/dates'
import Modal from './Modal.vue'

const props = defineProps({
  ouvert: { type: Boolean, default: false },
  absence: { type: Object, default: null },
  employeFixe: { type: Number, default: null },
  dateDebut: { type: String, default: '' }
})
const emit = defineEmits(['fermer', 'enregistre'])

const referentiel = useReferentielStore()
const form = reactive({ employe_id: null, motif_id: null, date_debut: '', date_reprise: '', commentaire: '' })
const erreur = ref('')
const enCours = ref(false)

const motifsProposes = computed(() =>
  referentiel.motifs.filter((m) => m.actif || m.id === props.absence?.motif_id))

watch(() => props.ouvert, async (ouvert) => {
  if (!ouvert) return
  erreur.value = ''
  Object.assign(form, {
    employe_id: props.absence?.employe_id ?? props.employeFixe,
    motif_id: props.absence?.motif_id ?? null,
    date_debut: props.absence?.date_debut ?? props.dateDebut,
    date_reprise: props.absence?.date_reprise ?? '',
    commentaire: props.absence?.commentaire ?? ''
  })
  await Promise.all([referentiel.chargerMotifs(), referentiel.employes.length ? null : referentiel.chargerEmployes()])
}, { immediate: true })

const enregistrer = async () => {
  erreur.value = ''
  enCours.value = true
  const payload = { ...form, date_reprise: form.date_reprise || null }
  try {
    if (props.absence?.id) {
      await api.put(`/absences/${props.absence.id}`, payload)
    } else {
      await api.post('/absences', payload)
    }
    emit('enregistre')
  } catch (error) {
    erreur.value = await messageErreur(error)
  } finally {
    enCours.value = false
  }
}

const supprimer = async () => {
  if (!confirm('Supprimer cette absence ?')) return
  enCours.value = true
  try {
    await api.delete(`/absences/${props.absence.id}`)
    emit('enregistre')
  } catch (error) {
    erreur.value = await messageErreur(error)
  } finally {
    enCours.value = false
  }
}
</script>
