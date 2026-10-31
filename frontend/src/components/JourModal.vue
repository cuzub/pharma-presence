<template>
  <Modal :ouvert="ouvert" :titre="titre" @fermer="$emit('fermer')">
    <div v-if="erreur" class="alert alert-danger py-2" role="alert">{{ erreur }}</div>
    <p v-if="ferieDuJour" class="alert alert-warning py-2 small mb-3"><i class="bi bi-flag"></i> Jour férié : {{ ferieDuJour }}</p>

    <h6 v-if="!vueEmploye">Heures en plus / en moins</h6>
    <p v-if="absenceBloquante" class="alert alert-secondary py-2 small mb-2" data-jour-bloque>
      Absent(e) ({{ absenceBloquante.motif_libelle }}) : saisie impossible ce jour-là.
    </p>
    <p v-else-if="verrouilleEmploye" class="alert alert-secondary py-2 small mb-2" data-jour-bloque>
      Ce mois est clôturé pour la saisie. Pour un oubli, adressez-vous à la pharmacienne.
    </p>
    <form :class="{ 'mb-4': !vueEmploye || regularisations.length }" data-saisie-jour @submit.prevent="enregistrer">
      <h6 v-if="vueEmploye" class="small fw-semibold mb-2">Heures +/-</h6>
      <div class="d-flex flex-wrap align-items-end gap-2">
        <div :class="{ 'champ-heures': vueEmploye }">
          <label v-if="!vueEmploye" for="jour-minutes" class="form-label small text-muted mb-1">
            Minutes (par 5 ; négatif = en moins)
          </label>
          <div class="input-group">
            <input
              id="jour-minutes"
              :aria-label="vueEmploye ? 'Heures +/-' : 'Minutes'"
              ref="champHeures"
              v-model="minutes"
              type="number"
              min="-720"
              max="720"
              step="5"
              class="form-control"
              placeholder="ex : 15 ou -30"
              :disabled="bloque"
            />
            <span class="input-group-text">min</span>
          </div>
        </div>
        <button v-if="!vueEmploye" type="submit" class="btn btn-primary" :disabled="enCours || bloque">Enregistrer</button>
        <button v-if="minutesInitiales && !vueEmploye" type="button" class="btn btn-outline-danger" :disabled="enCours || bloque" title="Effacer" @click="effacerHeures">
          <i class="bi bi-eraser"></i>
        </button>
      </div>
      <p class="form-text mb-0">
        <span v-if="apercu" :class="Number(minutes) < 0 ? 'minutes-moins' : 'minutes-plus'">Soit {{ apercu }}. </span>
        Ex. : 15 = 15 min en plus, -30 = 30 min en moins, 90 = 1h30 en plus.
      </p>

      <template v-if="vueEmploye">
        <h6 class="small fw-semibold mt-3 mb-2">Déplacement professionnel</h6>
        <div class="d-flex flex-wrap align-items-end gap-2">
          <div class="champ-motif">
            <label for="jour-motif" class="form-label small text-muted mb-1">Motif</label>
            <select id="jour-motif" v-model="motifChoix" class="form-select form-select-sm" :disabled="bloque">
              <option value="">Aucun</option>
              <option v-for="m in motifsProposes" :key="m.id" :value="m.id">{{ m.libelle }} — {{ formatNombre(m.km) }} km</option>
              <option :value="AUTRE">Autre (distance libre)</option>
            </select>
          </div>
          <div v-if="motifChoix === AUTRE" class="champ-motif">
            <label for="jour-precision" class="form-label small text-muted mb-1">Précision</label>
            <input id="jour-precision" v-model="motifPrecision" class="form-control form-control-sm" maxlength="255" required placeholder="ex : Pharmacie de Chartres" :disabled="bloque" />
          </div>
          <div class="champ-km">
            <label for="jour-km" class="form-label small text-muted mb-1">Km</label>
            <input
              v-if="motifChoix === AUTRE"
              id="jour-km"
              v-model="km"
              type="number"
              min="0.1"
              max="5000"
              step="0.1"
              class="form-control form-control-sm"
              required
              :disabled="bloque"
            />
            <input v-else id="jour-km" :value="kmAffiches" class="form-control form-control-sm" readonly tabindex="-1" />
          </div>
        </div>
        <p v-if="!referentiel.motifsDeplacement.length" class="form-text mb-0">
          Aucun motif enregistré : la pharmacienne peut en créer dans <em>Paramètres</em>.
        </p>
        <div class="d-flex justify-content-end mt-3">
          <button type="submit" class="btn btn-primary" :disabled="enCours || bloque">Enregistrer</button>
        </div>
      </template>
    </form>

    <div v-if="regularisations.length" :class="{ 'mb-4': !vueEmploye }" data-regularisations-jour>
      <h6 class="regularisation"><i class="bi bi-arrow-left-right"></i> Régularisations du jour</h6>
      <ul class="list-group list-group-flush mb-1">
        <li v-for="r in regularisations" :key="r.id" class="list-group-item d-flex gap-2 px-0 py-1">
          <span class="badge regularisation align-self-center">{{ formatMinutes(r.minutes) }}</span>
          <span class="small">{{ r.commentaire || 'Sans commentaire' }}</span>
        </li>
      </ul>
      <p class="form-text mb-0">
        {{ vueEmploye ? 'Saisies par la pharmacienne.' : 'À modifier depuis Employés → Heures +/-.' }}
      </p>
    </div>

    <template v-if="!vueEmploye">
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
    </template>

    <template v-if="!vueEmploye">
    <h6 class="mt-4">Déplacements du jour</h6>
    <ul v-if="deplacements.length" class="list-group list-group-flush mb-2">
      <li v-for="d in deplacements" :key="d.id" class="list-group-item d-flex align-items-center gap-2 px-0">
        <i class="bi bi-car-front"></i>
        <span class="flex-grow-1">{{ d.motif }} <span class="text-muted">— {{ formatNombre(d.km) }} km</span></span>
        <button v-if="deplacementModifiable(d)" type="button" class="btn btn-sm btn-outline-secondary" title="Modifier" :aria-label="`Modifier le déplacement ${d.motif}`" @click="$emit('modifier-deplacement', d)">
          <i class="bi bi-pencil"></i>
        </button>
      </li>
    </ul>
    <p v-else class="text-muted small mb-2">Aucun déplacement.</p>
    <button type="button" class="btn btn-sm btn-outline-primary" :disabled="bloque" @click="$emit('nouveau-deplacement', jour)">
      <i class="bi bi-plus-lg"></i> Ajouter un déplacement
    </button>
    </template>
  </Modal>
</template>

<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import api, { messageErreur } from '../services/api'
import { useReferentielStore } from '../stores/referentiel'
import { absenceBloquanteDuJour, absenceDuJour, ferie, formatFr, formatMinutes, formatNombre, saisieModifiableParEmploye } from '../utils/dates'
import Modal from './Modal.vue'

const props = defineProps({
  ouvert: { type: Boolean, default: false },
  employe: { type: Object, default: null },
  jour: { type: String, default: '' },
  // Vue de l'employé : pas de gestion des absences, saisie d'heures limitée à la fenêtre de clôture.
  vueEmploye: { type: Boolean, default: false },
  deplacementModifiable: { type: Function, default: () => true }
})
const emit = defineEmits(['fermer', 'modifie', 'nouvelle-absence', 'modifier-absence', 'nouveau-deplacement', 'modifier-deplacement'])

const minutes = ref('')
const erreur = ref('')
const enCours = ref(false)
const champHeures = ref(null)
const referentiel = useReferentielStore()
const AUTRE = 'autre'
const motifChoix = ref('')
const motifPrecision = ref('')
const km = ref('')

const minutesInitiales = computed(() => props.employe?.heures?.[props.jour] || 0)
const apercu = computed(() => (Number.isInteger(Number(minutes.value)) ? formatMinutes(Number(minutes.value)) : ''))
const absence = computed(() => (props.employe ? absenceDuJour(props.employe.absences, props.jour) : null))
const absenceBloquante = computed(() => (props.employe ? absenceBloquanteDuJour(props.employe.absences, props.jour) : null))
const verrouilleEmploye = computed(() => props.vueEmploye && !!props.jour && !saisieModifiableParEmploye(props.jour))
const bloque = computed(() => !!absenceBloquante.value || verrouilleEmploye.value)
const deplacements = computed(() => (props.employe?.deplacements || []).filter((d) => d.date === props.jour))
const regularisations = computed(() => (props.employe?.regularisations || []).filter((r) => r.jour === props.jour))
const ferieDuJour = computed(() => (props.jour ? ferie(props.jour) : null))
const titre = computed(() => props.employe ? `${props.employe.prenom} ${props.employe.nom} — ${formatFr(props.jour)}` : '')

// Vue employé : un seul déplacement par jour, saisi dans le même formulaire que les heures.
const deplacementJour = computed(() => deplacements.value[0] || null)
const motifsProposes = computed(() =>
  referentiel.motifsDeplacement.filter((m) => m.actif || m.id === deplacementJour.value?.motif_deplacement_id))
const kmAffiches = computed(() => {
  if (motifChoix.value === '') return ''
  const d = deplacementJour.value
  // Motif inchangé : on affiche les km enregistrés à l'origine (l'historique ne bouge pas).
  if (d && motifChoix.value === d.motif_deplacement_id) return formatNombre(d.km)
  const motif = referentiel.motifsDeplacement.find((m) => m.id === motifChoix.value)
  return motif ? formatNombre(motif.km) : ''
})

const initialiserDeplacement = async () => {
  const d = deplacementJour.value
  motifChoix.value = d ? (d.motif_deplacement_id ?? AUTRE) : ''
  motifPrecision.value = d && !d.motif_deplacement_id ? d.motif : ''
  km.value = d && !d.motif_deplacement_id ? d.km : ''
  try {
    await referentiel.chargerMotifsDeplacement(true)
  } catch (error) {
    erreur.value = await messageErreur(error)
  }
}

watch(() => props.ouvert, async (ouvert) => {
  if (!ouvert) return
  erreur.value = ''
  minutes.value = minutesInitiales.value || ''
  if (props.vueEmploye) initialiserDeplacement()
  await nextTick()
  champHeures.value?.focus()
})

const sauverHeures = (valeur) => api.put('/heures', { employe_id: props.employe.id, jour: props.jour, minutes: valeur })

const deplacementModifie = () => {
  const d = deplacementJour.value
  if (!d) return motifChoix.value !== ''
  if (motifChoix.value === '') return true
  if (motifChoix.value !== AUTRE) return motifChoix.value !== d.motif_deplacement_id
  return !!d.motif_deplacement_id || motifPrecision.value !== d.motif || Number(km.value) !== Number(d.km)
}

const enregistrerDeplacement = () => {
  const d = deplacementJour.value
  if (motifChoix.value === '') return api.delete(`/deplacements/${d.id}`)
  const autre = motifChoix.value === AUTRE
  const corps = {
    date: props.jour,
    motif_deplacement_id: autre ? null : motifChoix.value,
    motif: autre ? motifPrecision.value : null,
    km: autre ? km.value : null
  }
  return d ? api.put(`/deplacements/${d.id}`, corps) : api.post('/deplacements', corps)
}

const executer = async (action) => {
  erreur.value = ''
  enCours.value = true
  try {
    await action()
    emit('modifie')
  } catch (error) {
    erreur.value = await messageErreur(error)
  } finally {
    enCours.value = false
  }
}

const enregistrer = () => {
  if (props.vueEmploye && motifChoix.value === '' && deplacementJour.value
    && !confirm(`Supprimer le déplacement du ${formatFr(props.jour)} (${deplacementJour.value.motif}) ?`)) return
  executer(async () => {
    const valeur = minutes.value === '' ? 0 : Number(minutes.value)
    if (!props.vueEmploye || valeur !== minutesInitiales.value) await sauverHeures(valeur)
    if (props.vueEmploye && deplacementModifie()) await enregistrerDeplacement()
  })
}

const effacerHeures = () => executer(() => sauverHeures(0))
</script>

<style scoped>
.champ-motif {
  flex: 1 1 12rem;
}

.champ-heures {
  width: 14rem;
}

.champ-km {
  width: 7rem;
}
</style>

