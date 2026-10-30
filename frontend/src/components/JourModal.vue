<template>
  <Modal :ouvert="ouvert" :titre="titre" @fermer="$emit('fermer')">
    <div v-if="erreur" class="alert alert-danger py-2" role="alert">{{ erreur }}</div>
    <p v-if="ferieDuJour" class="alert alert-warning py-2 small mb-3"><i class="bi bi-flag"></i> Jour férié : {{ ferieDuJour }}</p>

    <h6>Heures en plus</h6>
    <form class="d-flex align-items-end gap-2 mb-4" @submit.prevent="enregistrerHeures">
      <div>
        <label for="jour-heures" class="form-label small text-muted mb-1">Nombre d'heures (au quart d'heure)</label>
        <div class="input-group">
          <input id="jour-heures" ref="champHeures" v-model="heures" type="number" min="0" max="24" step="0.25" class="form-control" placeholder="0" />
          <span class="input-group-text">h</span>
        </div>
      </div>
      <button type="submit" class="btn btn-primary" :disabled="enCours">Enregistrer</button>
      <button v-if="heuresInitiales" type="button" class="btn btn-outline-danger" :disabled="enCours" title="Effacer" @click="effacerHeures">
        <i class="bi bi-eraser"></i>
      </button>
    </form>

    <h6>Absence</h6>
    <div v-if="absence" class="d-flex flex-wrap align-items-center gap-2">
      <span class="pastille-motif" :style="{ background: absence.motif_couleur }">{{ absence.motif_libelle }}</span>
      <span class="small">
        du {{ formatFr(absence.date_debut) }}
        — {{ absence.date_reprise ? `reprise le ${formatFr(absence.date_reprise)}` : 'en cours' }}
      </span>
      <button type="button" class="btn btn-sm btn-outline-secondary ms-auto" @click="$emit('modifier-absence', absence)">
        <i class="bi bi-pencil"></i> Modifier
      </button>
    </div>
    <div v-else>
      <p class="text-muted small mb-2">Présent(e) ce jour-là (aucune absence).</p>
      <button type="button" class="btn btn-sm btn-outline-primary" @click="$emit('nouvelle-absence', jour)">
        <i class="bi bi-calendar-plus"></i> Déclarer une absence à partir de ce jour
      </button>
    </div>
  </Modal>
</template>

<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import api, { messageErreur } from '../services/api'
import { absenceDuJour, ferie, formatFr } from '../utils/dates'
import Modal from './Modal.vue'

const props = defineProps({
  ouvert: { type: Boolean, default: false },
  employe: { type: Object, default: null },
  jour: { type: String, default: '' }
})
const emit = defineEmits(['fermer', 'modifie', 'nouvelle-absence', 'modifier-absence'])

const heures = ref('')
const erreur = ref('')
const enCours = ref(false)
const champHeures = ref(null)

const heuresInitiales = computed(() => props.employe?.heures?.[props.jour] || 0)
const absence = computed(() => (props.employe ? absenceDuJour(props.employe.absences, props.jour) : null))
const ferieDuJour = computed(() => (props.jour ? ferie(props.jour) : null))
const titre = computed(() => props.employe ? `${props.employe.prenom} ${props.employe.nom} — ${formatFr(props.jour)}` : '')

watch(() => props.ouvert, async (ouvert) => {
  if (!ouvert) return
  erreur.value = ''
  heures.value = heuresInitiales.value || ''
  await nextTick()
  champHeures.value?.focus()
})

const envoyer = async (valeur) => {
  erreur.value = ''
  enCours.value = true
  try {
    await api.put('/heures', { employe_id: props.employe.id, jour: props.jour, heures: valeur })
    emit('modifie')
  } catch (error) {
    erreur.value = await messageErreur(error)
  } finally {
    enCours.value = false
  }
}

const enregistrerHeures = () => envoyer(heures.value === '' ? 0 : heures.value)
const effacerHeures = () => envoyer(0)
</script>
