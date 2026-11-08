<template>
  <Modal :ouvert="ouvert" :titre="titre" @fermer="$emit('fermer')">
    <div v-if="erreur" class="alert alert-danger py-2" role="alert">{{ erreur }}</div>
    <p v-if="ferieDuJour" class="alert alert-warning py-2 small mb-3"><i class="bi bi-flag"></i> Jour férié : {{ ferieDuJour }}</p>

    <h6 v-if="!vueEmploye && !ligneAdmin">Heures en plus / en moins</h6>
    <p v-if="!ligneAdmin && horsContrat" class="alert alert-secondary py-2 small mb-2" data-jour-bloque>
      Pas de contrat ce jour-là : saisie impossible.
    </p>
    <p v-else-if="!ligneAdmin && absenceBloquante" class="alert alert-secondary py-2 small mb-2" data-jour-bloque>
      Absent(e) ({{ absenceBloquante.motif_libelle }}) : saisie impossible ce jour-là.
    </p>
    <p v-else-if="!ligneAdmin && verrouilleEmploye" class="alert alert-secondary py-2 small mb-2" data-jour-bloque>
      Ce mois est clôturé pour la saisie. Pour un oubli, adressez-vous à Elise.
    </p>
    <p v-else-if="!ligneAdmin && blocageEmploye" class="alert alert-secondary py-2 small mb-2" data-jour-bloque>
      {{ MOTIFS_BLOCAGE[blocageEmploye] }}
    </p>
    <form data-saisie-jour @submit.prevent="enregistrer">
      <template v-if="!ligneAdmin">
        <h6 v-if="vueEmploye" class="small fw-semibold mb-2">Heures +/-</h6>
        <div class="d-flex flex-wrap align-items-end gap-2">
          <div :class="{ 'champ-heures': vueEmploye }">
            <label v-if="!vueEmploye" for="jour-minutes" class="form-label small text-muted mb-1">
              Minutes (par 5 ; négatif = en moins)
            </label>
            <div class="input-group input-group-sm">
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
          <button v-if="minutes !== ''" type="button" class="btn btn-outline-danger btn-sm" :disabled="bloque" title="Vider le champ (à enregistrer)" data-effacer-heures @click="viderHeures">
            <i class="bi bi-eraser"></i>
          </button>
        </div>
        <p class="form-text mb-0">
          <span v-if="apercu" :class="Number(minutes) < 0 ? 'minutes-moins' : 'minutes-plus'">Soit {{ apercu }}. </span>
          Ex. : 15 = 15 min en plus, -30 = 30 min en moins, 90 = 1h30 en plus.
        </p>
      </template>

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
          <div class="input-group input-group-sm">
            <input
              v-if="motifChoix === AUTRE"
              id="jour-km"
              v-model="km"
              type="number"
              min="0.1"
              max="5000"
              step="0.1"
              class="form-control"
              required
              :disabled="bloque"
            />
            <input v-else id="jour-km" :value="kmAffiches" class="form-control" readonly tabindex="-1" />
            <span class="input-group-text">km</span>
          </div>
        </div>
        <button v-if="motifChoix !== ''" type="button" class="btn btn-outline-danger btn-sm" :disabled="bloque" title="Vider le déplacement (à enregistrer)" data-effacer-deplacement @click="viderDeplacement">
          <i class="bi bi-eraser"></i>
        </button>
      </div>
      <p v-if="!referentiel.motifsDeplacement.length" class="form-text mb-0">
        Aucun motif enregistré : Elise peut en créer dans <em>Paramètres</em>.
      </p>
      <div class="d-flex justify-content-end mt-3">
        <button type="submit" class="btn btn-primary" :disabled="enCours || bloque">Enregistrer</button>
      </div>
    </form>

    <div v-if="!ligneAdmin && regularisations.length" :class="{ 'mb-4': !vueEmploye }" data-regularisations-jour>
      <h6 class="regularisation"><i class="bi bi-arrow-left-right"></i> Régularisations du jour</h6>
      <ul class="list-group list-group-flush mb-1">
        <li v-for="r in regularisations" :key="r.id" class="list-group-item d-flex gap-2 px-0 py-1">
          <span class="badge regularisation align-self-center">{{ formatMinutes(r.minutes) }}</span>
          <span class="small">{{ r.commentaire || 'Sans commentaire' }}</span>
        </li>
      </ul>
      <p class="form-text mb-0">
        {{ vueEmploye ? 'Saisies par Elise.' : 'À modifier depuis Employés → Heures +/-.' }}
      </p>
    </div>

  </Modal>
</template>

<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import api, { messageErreur } from '../services/api'
import { useReferentielStore } from '../stores/referentiel'
import { absenceBloquanteDuJour, blocageJourEmploye, ferie, formatFr, formatMinutes, formatNombre, saisieModifiableParEmploye } from '../utils/dates'
import Modal from './Modal.vue'

const props = defineProps({
  ouvert: { type: Boolean, default: false },
  employe: { type: Object, default: null },
  jour: { type: String, default: '' },
  // Vue de l'employé : saisie limitée à la fenêtre de clôture et aux jours ouverts.
  vueEmploye: { type: Boolean, default: false },
  joursFermeture: { type: Array, default: () => [] },
  // Ligne IK d'un admin : déplacement seul, ni heures, ni contrat, ni absence.
  ligneAdmin: { type: Boolean, default: false }
})
const emit = defineEmits(['fermer', 'modifie'])

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
const absenceBloquante = computed(() => (props.employe ? absenceBloquanteDuJour(props.employe.absences, props.jour) : null))
const verrouilleEmploye = computed(() => props.vueEmploye && !!props.jour && !saisieModifiableParEmploye(props.jour))
const blocageEmploye = computed(() => (props.vueEmploye && props.jour ? blocageJourEmploye(props.jour, props.joursFermeture) : null))
const MOTIFS_BLOCAGE = {
  future: 'Date future : saisie impossible.',
  dimanche: 'Dimanche : saisie impossible.',
  ferie: 'Jour férié : saisie impossible.',
  fermeture: 'Jour de fermeture de la pharmacie : saisie impossible.'
}
const horsContrat = computed(() => !props.ligneAdmin && !!props.employe && !!props.jour
  && !(props.employe.contrats || []).some((c) => c.date_debut <= props.jour && (!c.date_fin || c.date_fin >= props.jour)))
const bloque = computed(() => !!absenceBloquante.value || verrouilleEmploye.value || horsContrat.value || !!blocageEmploye.value)
const deplacements = computed(() => (props.employe?.deplacements || []).filter((d) => d.date === props.jour))
const regularisations = computed(() => (props.employe?.regularisations || []).filter((r) => r.jour === props.jour))
const ferieDuJour = computed(() => (props.jour ? ferie(props.jour) : null))
const titre = computed(() => {
  if (!props.employe) return ''
  if (props.ligneAdmin) return `${props.employe.nom} — Déplacement — ${formatFr(props.jour)}`
  return `${props.employe.prenom} ${props.employe.nom} — ${formatFr(props.jour)}`
})

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
  initialiserDeplacement()
  await nextTick()
  if (!props.ligneAdmin) champHeures.value?.focus()
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
    km: autre ? km.value : null,
    ...(props.ligneAdmin ? { utilisateur_id: props.employe.id } : props.vueEmploye ? {} : { employe_id: props.employe.id })
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

const enregistrer = () => executer(async () => {
  const valeur = minutes.value === '' ? 0 : Number(minutes.value)
  if (!props.ligneAdmin && (!props.vueEmploye || valeur !== minutesInitiales.value)) await sauverHeures(valeur)
  if (deplacementModifie()) await enregistrerDeplacement()
})

// Remise à zéro du formulaire uniquement : la suppression se fait à l'enregistrement.
const viderHeures = () => {
  minutes.value = ''
}
const viderDeplacement = () => {
  motifChoix.value = ''
  motifPrecision.value = ''
  km.value = ''
}
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

