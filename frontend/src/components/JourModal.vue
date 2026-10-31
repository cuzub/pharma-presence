<template>
  <Modal :ouvert="ouvert" :titre="titre" @fermer="$emit('fermer')">
    <div v-if="erreur" class="alert alert-danger py-2" role="alert">{{ erreur }}</div>
    <p v-if="ferieDuJour" class="alert alert-warning py-2 small mb-3"><i class="bi bi-flag"></i> Jour férié : {{ ferieDuJour }}</p>

    <h6>Heures en plus / en moins</h6>
    <form class="d-flex flex-wrap align-items-end gap-2 mb-1" @submit.prevent="enregistrerHeures">
      <div>
        <label for="jour-minutes" class="form-label small text-muted mb-1">Minutes (par 5 ; négatif = en moins)</label>
        <div class="input-group">
          <input
            id="jour-minutes"
            ref="champHeures"
            v-model="minutes"
            type="number"
            min="-720"
            max="720"
            step="5"
            class="form-control"
            placeholder="ex : 15 ou -30"
          />
          <span class="input-group-text">min</span>
        </div>
      </div>
      <button type="submit" class="btn btn-primary" :disabled="enCours">Enregistrer</button>
      <button v-if="minutesInitiales" type="button" class="btn btn-outline-danger" :disabled="enCours" title="Effacer" @click="effacerHeures">
        <i class="bi bi-eraser"></i>
      </button>
    </form>
    <p class="form-text mb-4">
      <span v-if="apercu" :class="Number(minutes) < 0 ? 'minutes-moins' : 'minutes-plus'">Soit {{ apercu }}. </span>
      Ex. : 15 = 15 min en plus, -30 = 30 min en moins, 90 = 1h30 en plus.
    </p>

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

    <h6 class="mt-4">Déplacements du jour</h6>
    <ul v-if="deplacements.length" class="list-group list-group-flush mb-2">
      <li v-for="d in deplacements" :key="d.id" class="list-group-item d-flex align-items-center gap-2 px-0">
        <i class="bi bi-car-front"></i>
        <span class="flex-grow-1">{{ d.motif }} <span class="text-muted">— {{ formatNombre(d.km) }} km</span></span>
        <button type="button" class="btn btn-sm btn-outline-secondary" title="Modifier" :aria-label="`Modifier le déplacement ${d.motif}`" @click="$emit('modifier-deplacement', d)">
          <i class="bi bi-pencil"></i>
        </button>
      </li>
    </ul>
    <p v-else class="text-muted small mb-2">Aucun déplacement.</p>
    <button type="button" class="btn btn-sm btn-outline-primary" @click="$emit('nouveau-deplacement', jour)">
      <i class="bi bi-plus-lg"></i> Ajouter un déplacement
    </button>
  </Modal>
</template>

<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import api, { messageErreur } from '../services/api'
import { absenceDuJour, ferie, formatFr, formatMinutes, formatNombre } from '../utils/dates'
import Modal from './Modal.vue'

const props = defineProps({
  ouvert: { type: Boolean, default: false },
  employe: { type: Object, default: null },
  jour: { type: String, default: '' }
})
const emit = defineEmits(['fermer', 'modifie', 'nouvelle-absence', 'modifier-absence', 'nouveau-deplacement', 'modifier-deplacement'])

const minutes = ref('')
const erreur = ref('')
const enCours = ref(false)
const champHeures = ref(null)

const minutesInitiales = computed(() => props.employe?.heures?.[props.jour] || 0)
const apercu = computed(() => (Number.isInteger(Number(minutes.value)) ? formatMinutes(Number(minutes.value)) : ''))
const absence = computed(() => (props.employe ? absenceDuJour(props.employe.absences, props.jour) : null))
const deplacements = computed(() => (props.employe?.deplacements || []).filter((d) => d.date === props.jour))
const ferieDuJour = computed(() => (props.jour ? ferie(props.jour) : null))
const titre = computed(() => props.employe ? `${props.employe.prenom} ${props.employe.nom} — ${formatFr(props.jour)}` : '')

watch(() => props.ouvert, async (ouvert) => {
  if (!ouvert) return
  erreur.value = ''
  minutes.value = minutesInitiales.value || ''
  await nextTick()
  champHeures.value?.focus()
})

const envoyer = async (valeur) => {
  erreur.value = ''
  enCours.value = true
  try {
    await api.put('/heures', { employe_id: props.employe.id, jour: props.jour, minutes: valeur })
    emit('modifie')
  } catch (error) {
    erreur.value = await messageErreur(error)
  } finally {
    enCours.value = false
  }
}

const enregistrerHeures = () => envoyer(minutes.value === '' ? 0 : Number(minutes.value))
const effacerHeures = () => envoyer(0)
</script>
