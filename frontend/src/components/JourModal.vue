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
        <div v-if="regularisations.length" class="mt-3" data-regularisations-jour>
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
      </template>

      <h6 class="small fw-semibold mt-3 mb-2">Déplacements professionnels</h6>
      <div v-for="(ligne, i) in lignes" :key="ligne.cle" class="d-flex flex-wrap align-items-end gap-2 mb-2" data-ligne-deplacement>
        <div class="champ-motif">
          <label :for="idChamp('jour-motif', i)" class="form-label small text-muted mb-1" :class="{ 'visually-hidden': i > 0 }">Motif</label>
          <select :id="idChamp('jour-motif', i)" v-model="ligne.motifChoix" class="form-select form-select-sm" :disabled="bloque">
            <option value="">Aucun</option>
            <option v-for="m in motifsProposes" :key="m.id" :value="m.id">{{ m.libelle }} — {{ formatNombre(m.km) }} km</option>
            <option :value="AUTRE">Autre (distance libre)</option>
          </select>
        </div>
        <div v-if="ligne.motifChoix === AUTRE" class="champ-motif">
          <label :for="idChamp('jour-precision', i)" class="form-label small text-muted mb-1" :class="{ 'visually-hidden': i > 0 }">Précision</label>
          <input :id="idChamp('jour-precision', i)" v-model="ligne.motifPrecision" class="form-control form-control-sm" maxlength="255" required placeholder="ex : Pharmacie de Chartres" :disabled="bloque" />
        </div>
        <div class="champ-km">
          <label :for="idChamp('jour-km', i)" class="form-label small text-muted mb-1" :class="{ 'visually-hidden': i > 0 }">Km</label>
          <div class="input-group input-group-sm">
            <input
              v-if="ligne.motifChoix === AUTRE"
              :id="idChamp('jour-km', i)"
              v-model="ligne.km"
              type="number"
              min="0.1"
              max="5000"
              step="0.1"
              class="form-control"
              required
              :disabled="bloque"
            />
            <input v-else :id="idChamp('jour-km', i)" :value="kmAffiches(ligne)" class="form-control" readonly tabindex="-1" />
            <span class="input-group-text">km</span>
          </div>
        </div>
        <button type="button" class="btn btn-outline-danger btn-sm" :disabled="bloque" title="Retirer ce déplacement (à enregistrer)" aria-label="Retirer ce déplacement" data-retirer-deplacement @click="retirerLigne(i)">
          <i class="bi bi-dash-lg"></i>
        </button>
      </div>
      <button type="button" class="btn btn-outline-primary btn-sm" :disabled="bloque" title="Ajouter un déplacement" data-ajouter-deplacement @click="ajouterLigne">
        <i class="bi bi-plus-lg"></i> Ajouter un déplacement
      </button>
      <p v-if="!referentiel.motifsDeplacement.length" class="form-text mb-0">
        Aucun motif enregistré : Elise peut en créer dans <em>Paramètres</em>.
      </p>

      <p v-if="vueEmploye && lignesPlanning.length" class="small text-muted mt-3 mb-0" data-horaires-prevus>
        <i class="bi bi-calendar-week"></i> Planning : {{ lignesPlanning.join(' · ') }}
      </p>
      <fieldset v-if="!vueEmploye" class="mt-3 pt-3 border-top" data-horaires-jour :disabled="bloque">
      <h6 class="small fw-semibold mb-1">
        Horaires de présence (planning)
        <span v-if="entreePlanning?.exception" class="badge text-bg-dark ms-1">Exceptionnel</span>
      </h6>
      <p class="form-text mt-0 mb-2">
        Pour un événement exceptionnel ce jour-là (matin {{ PLAGES.matin.join('–') }}, après-midi {{ PLAGES.apres_midi.join('–') }}).
        Laisser vide = pas présent(e) sur la demi-journée.
      </p>
      <div v-for="demi in demisDuJour" :key="demi" class="d-flex flex-wrap align-items-center gap-2 mb-2">
        <span class="small champ-demi">{{ LIBELLES_DEMI_JOURNEE[demi] }}</span>
        <input v-model="horaires[demi][0]" type="time" step="300" :min="PLAGES[demi][0]" :max="PLAGES[demi][1]" class="form-control form-control-sm champ-heure" :aria-label="`${LIBELLES_DEMI_JOURNEE[demi]} : début`" />
        <span class="small">à</span>
        <input v-model="horaires[demi][1]" type="time" step="300" :min="PLAGES[demi][0]" :max="PLAGES[demi][1]" class="form-control form-control-sm champ-heure" :aria-label="`${LIBELLES_DEMI_JOURNEE[demi]} : fin`" />
        <button type="button" class="btn btn-outline-secondary btn-sm" title="Vider (pas présent)" :aria-label="`Vider le ${LIBELLES_DEMI_JOURNEE[demi]}`" @click="horaires[demi] = ['', '']">
          <i class="bi bi-eraser"></i>
        </button>
      </div>
      <div v-if="entreePlanning?.exception" class="d-flex justify-content-end">
        <button type="button" class="btn btn-outline-secondary btn-sm" :disabled="enCours" data-planning-habituel @click="revenirAuPlanning">
          Revenir au planning habituel
        </button>
      </div>
      </fieldset>

      <div class="d-flex justify-content-end mt-3">
        <button type="submit" class="btn btn-primary" :disabled="enCours || bloque">Enregistrer</button>
      </div>
    </form>
  </Modal>
</template>

<script setup>
import { computed, nextTick, reactive, ref, watch } from 'vue'
import api, { messageErreur } from '../services/api'
import { useReferentielStore } from '../stores/referentiel'
import { absenceBloquanteDuJour, blocageJourEmploye, ferie, formatFr, formatMinutes, formatNombre, saisieModifiableParEmploye } from '../utils/dates'
import { DEMI_JOURNEES, LIBELLES_DEMI_JOURNEE, PLAGES, demiJourneesDuJour, lignesHoraires } from '../utils/planning'
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
const lignes = ref([])
const aSupprimer = ref([])
let prochaineCle = 0

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
  if (props.ligneAdmin) return `${props.employe.nom} — Planning et déplacements — ${formatFr(props.jour)}`
  return `${props.employe.prenom} ${props.employe.nom} — ${formatFr(props.jour)}`
})

const motifsProposes = computed(() => {
  const utilises = new Set(deplacements.value.map((d) => d.motif_deplacement_id))
  return referentiel.motifsDeplacement.filter((m) => m.actif || utilises.has(m.id))
})
// La première ligne garde les identifiants historiques des champs.
const idChamp = (base, i) => (i ? `${base}-${i}` : base)
const kmAffiches = (ligne) => {
  if (ligne.motifChoix === '') return ''
  const d = ligne.original
  // Motif inchangé : on affiche les km enregistrés à l'origine (l'historique ne bouge pas).
  if (d && ligne.motifChoix === d.motif_deplacement_id) return formatNombre(d.km)
  const motif = referentiel.motifsDeplacement.find((m) => m.id === ligne.motifChoix)
  return motif ? formatNombre(motif.km) : ''
}

const nouvelleLigne = (d = null) => ({
  cle: prochaineCle++,
  original: d,
  motifChoix: d ? (d.motif_deplacement_id ?? AUTRE) : '',
  motifPrecision: d && !d.motif_deplacement_id ? d.motif : '',
  km: d && !d.motif_deplacement_id ? d.km : ''
})
const ajouterLigne = () => lignes.value.push(nouvelleLigne())
const retirerLigne = (i) => {
  const [ligne] = lignes.value.splice(i, 1)
  if (ligne.original) aSupprimer.value.push(ligne.original)
}

const initialiserDeplacement = async () => {
  lignes.value = deplacements.value.length ? deplacements.value.map(nouvelleLigne) : [nouvelleLigne()]
  aSupprimer.value = []
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
  initialiserHoraires()
  initialiserDeplacement()
  await nextTick()
  if (!props.ligneAdmin) champHeures.value?.focus()
})

const sauverHeures = (valeur) => api.put('/heures', { employe_id: props.employe.id, jour: props.jour, minutes: valeur })

const ligneModifiee = (ligne) => {
  const d = ligne.original
  if (!d) return true
  if (ligne.motifChoix !== AUTRE) return ligne.motifChoix !== d.motif_deplacement_id
  return !!d.motif_deplacement_id || ligne.motifPrecision !== d.motif || Number(ligne.km) !== Number(d.km)
}

// Chaque requête réussie met l'état à jour : une nouvelle tentative après erreur ne crée pas de doublon.
const enregistrerDeplacements = async () => {
  while (aSupprimer.value.length) {
    await api.delete(`/deplacements/${aSupprimer.value[0].id}`)
    aSupprimer.value.shift()
  }
  for (const ligne of lignes.value) {
    if (ligne.motifChoix === '') {
      if (ligne.original) {
        await api.delete(`/deplacements/${ligne.original.id}`)
        ligne.original = null
      }
      continue
    }
    if (!ligneModifiee(ligne)) continue
    const autre = ligne.motifChoix === AUTRE
    const corps = {
      date: props.jour,
      motif_deplacement_id: autre ? null : ligne.motifChoix,
      motif: autre ? ligne.motifPrecision : null,
      km: autre ? ligne.km : null,
      ...(props.ligneAdmin ? { utilisateur_id: props.employe.id } : props.vueEmploye ? {} : { employe_id: props.employe.id })
    }
    const { data } = ligne.original
      ? await api.put(`/deplacements/${ligne.original.id}`, corps)
      : await api.post('/deplacements', corps)
    ligne.original = data
  }
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
  await enregistrerDeplacements()
  if (!props.vueEmploye && horairesModifies()) await enregistrerHoraires()
})

// Remise à zéro du formulaire uniquement : la suppression se fait à l'enregistrement.
const viderHeures = () => {
  minutes.value = ''
}

// --- Horaires du jour (exception au planning) --------------------------------
const entreePlanning = computed(() => props.employe?.planning?.[props.jour] || null)
const lignesPlanning = computed(() => lignesHoraires(entreePlanning.value))
const demisDuJour = computed(() => (props.jour ? demiJourneesDuJour(props.jour) : []))
const horaires = reactive({ matin: ['', ''], apres_midi: ['', ''] })
let horairesInitiaux = ''
const instantaneHoraires = () => JSON.stringify(DEMI_JOURNEES.map((demi) => horaires[demi]))
const initialiserHoraires = () => {
  for (const demi of DEMI_JOURNEES) horaires[demi] = [...(entreePlanning.value?.[demi] || ['', ''])]
  horairesInitiaux = instantaneHoraires()
}
// Sans modification, on n'enregistre rien : cela créerait une exception au planning habituel.
const horairesModifies = () => instantaneHoraires() !== horairesInitiaux
const titulairePlanning = () => (props.ligneAdmin ? { utilisateur_id: props.employe.id } : { employe_id: props.employe.id })
const demiJourneeSaisie = (demi) => (horaires[demi].some(Boolean) ? horaires[demi] : null)

const enregistrerHoraires = async () => {
  await api.put('/planning/exceptions', {
    ...titulairePlanning(),
    jour: props.jour,
    matin: demiJourneeSaisie('matin'),
    apres_midi: demisDuJour.value.includes('apres_midi') ? demiJourneeSaisie('apres_midi') : null
  })
  horairesInitiaux = instantaneHoraires()
}

const revenirAuPlanning = () => executer(() => api.delete('/planning/exceptions', {
  params: { ...titulairePlanning(), jour: props.jour }
}))
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

.champ-demi {
  width: 5.5rem;
}

.champ-heure {
  width: 7rem;
}
</style>

