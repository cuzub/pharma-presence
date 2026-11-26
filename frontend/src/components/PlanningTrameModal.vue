<template>
  <Modal :ouvert="!!titulaire" :titre="`Planning — ${titulaire?.nom || ''}`" taille="xl" @fermer="$emit('fermer')">
    <div v-if="erreur" class="alert alert-danger py-2" role="alert">{{ erreur }}</div>
    <div v-if="message" class="alert alert-success py-2" role="status">{{ message }}</div>

    <div class="d-flex flex-wrap align-items-end gap-3 mb-3">
      <div v-if="trames.length">
        <label for="pt-trame" class="form-label small text-muted mb-1">Planning</label>
        <select id="pt-trame" v-model="trameId" class="form-select form-select-sm" @change="choisir">
          <option v-for="t in trames" :key="t.id" :value="t.id">À partir du {{ formatFr(t.date_debut) }}</option>
        </select>
      </div>
      <div v-else-if="demanderDate">
        <label for="pt-debut" class="form-label small text-muted mb-1">Applicable à partir du</label>
        <input id="pt-debut" v-model="dateDebut" type="date" class="form-control form-control-sm" required />
      </div>
      <button type="button" class="btn btn-outline-secondary btn-sm" title="Recopier les horaires de la semaine 1 dans la semaine 2" @click="copierSemaine">
        <i class="bi bi-copy"></i> Semaine 1 → semaine 2
      </button>
    </div>
    <p class="form-text mt-0">
      Semaine 1 = semaines impaires, semaine 2 = semaines paires (numéro de semaine du calendrier).
      Matin de {{ PLAGES.matin[0] }} à {{ PLAGES.matin[1] }}, après-midi de {{ PLAGES.apres_midi[0] }} à {{ PLAGES.apres_midi[1] }} ;
      le samedi, le matin seulement.
      <template v-if="!trames.length && !demanderDate">Ces horaires s'appliqueront à partir du {{ formatFr(dateDebut) }}.</template>
    </p>

    <fieldset v-if="choixOuvert" class="border rounded p-3 mb-3" data-choix-application>
      <legend class="float-none w-auto fs-6 px-2 mb-0">Ces horaires s'appliquent…</legend>
      <div class="form-check">
        <input id="pt-mode-corriger" v-model="mode" class="form-check-input" type="radio" value="corriger" />
        <label for="pt-mode-corriger" class="form-check-label">Corriger le planning « à partir du {{ formatFr(trameCourante?.date_debut) }} » (sans nouvelle période)</label>
      </div>
      <div class="form-check">
        <input id="pt-mode-nouveau" v-model="mode" class="form-check-input" type="radio" value="nouveau" />
        <label for="pt-mode-nouveau" class="form-check-label">Nouveau planning à partir du</label>
        <input id="pt-nouvelle-date" v-model="dateDebut" type="date" class="form-control form-control-sm d-inline-block w-auto ms-2" :disabled="mode !== 'nouveau'" :required="mode === 'nouveau'" aria-label="Date d'application du nouveau planning" />
      </div>
      <div class="form-text">L'ancien planning reste valable jusqu'à la veille de cette date.</div>
    </fieldset>

    <form id="form-trame" class="row g-3" @submit.prevent="valider">
      <div v-for="semaine in ['1', '2']" :key="semaine" class="col-lg-6" :data-semaine="semaine">
        <h6 class="mb-2">Semaine {{ semaine }} <span class="text-muted small">({{ semaine === '1' ? 'impaire' : 'paire' }}) — {{ formatDuree(totalSemaine(semaine)) }}</span></h6>
        <table class="table table-sm align-middle mb-0">
          <thead>
            <tr class="small text-muted">
              <th></th>
              <th>Matin</th>
              <th>Après-midi</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(jour, index) in edition[semaine]" :key="index">
              <th class="small">{{ JOURS_COURTS[index] }}</th>
              <td v-for="demi in DEMI_JOURNEES" :key="demi">
                <div v-if="demi === 'matin' || index !== SAMEDI" class="d-flex align-items-center gap-1">
                  <input v-model="jour[demi][0]" type="time" step="300" :min="PLAGES[demi][0]" :max="PLAGES[demi][1]" class="form-control form-control-sm" :aria-label="`Semaine ${semaine}, ${JOURS_COURTS[index]}, ${LIBELLES_DEMI_JOURNEE[demi]} : début`" />
                  <span class="small">–</span>
                  <input v-model="jour[demi][1]" type="time" step="300" :min="PLAGES[demi][0]" :max="PLAGES[demi][1]" class="form-control form-control-sm" :aria-label="`Semaine ${semaine}, ${JOURS_COURTS[index]}, ${LIBELLES_DEMI_JOURNEE[demi]} : fin`" />
                  <button v-if="jour[demi].some(Boolean)" type="button" class="btn btn-link btn-sm p-0 text-secondary" title="Vider" :aria-label="`Vider ${JOURS_COURTS[index]} ${LIBELLES_DEMI_JOURNEE[demi]}`" @click="jour[demi] = ['', '']">
                    <i class="bi bi-x-lg"></i>
                  </button>
                </div>
                <span v-else class="small text-muted">—</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </form>

    <template #footer>
      <button v-if="trameId && !choixOuvert" type="button" class="btn btn-outline-danger me-auto" @click="supprimer">Supprimer ce planning</button>
      <button v-if="choixOuvert" type="button" class="btn btn-outline-secondary" @click="choixOuvert = false">Retour</button>
      <button v-else type="button" class="btn btn-outline-secondary" @click="$emit('fermer')">Fermer</button>
      <button type="submit" form="form-trame" class="btn btn-primary" :disabled="enCours">Enregistrer</button>
    </template>
  </Modal>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import api, { messageErreur } from '../services/api'
import { JOURS_COURTS, aujourdhuiIso, formatFr } from '../utils/dates'
import { DEMI_JOURNEES, LIBELLES_DEMI_JOURNEE, PLAGES, SAMEDI, formatDuree, minutesDe } from '../utils/planning'
import Modal from './Modal.vue'

// titulaire : { employe_id, nom, date_entree } pour un employé, { nom } pour le planning de l'admin connecté.
const props = defineProps({ titulaire: { type: Object, default: null } })
const emit = defineEmits(['fermer', 'modifie'])

const trames = ref([])
const trameId = ref(null)
const dateDebut = ref('')
const demanderDate = ref(false)
const choixOuvert = ref(false)
const mode = ref('corriger')
const edition = ref({ 1: [], 2: [] })
const erreur = ref('')
const message = ref('')
const enCours = ref(false)

const jourVide = () => ({ matin: ['', ''], apres_midi: ['', ''] })
const versEdition = (horaires) => Object.fromEntries(['1', '2'].map((s) => [
  s, Array.from({ length: SAMEDI + 1 }, (_, i) => {
    const jour = horaires?.[s]?.[i] || {}
    return { matin: [...(jour.matin || ['', ''])], apres_midi: [...(jour.apres_midi || ['', ''])] }
  })
]))
const versApi = () => Object.fromEntries(['1', '2'].map((s) => [
  s, edition.value[s].map((jour, i) => ({
    matin: jour.matin.some(Boolean) ? jour.matin : null,
    apres_midi: i !== SAMEDI && jour.apres_midi.some(Boolean) ? jour.apres_midi : null
  }))
]))

const totalSemaine = (semaine) => edition.value[semaine].reduce((total, jour, i) => total + DEMI_JOURNEES
  .filter((d) => d === 'matin' || i !== SAMEDI)
  .reduce((somme, d) => {
    const [debut, fin] = jour[d]
    return debut && fin && fin > debut ? somme + minutesDe(fin) - minutesDe(debut) : somme
  }, 0), 0)

const trameCourante = computed(() => trames.value.find((t) => t.id === trameId.value))

// Sans planning : début d'année, sauf pour un employé entré depuis (on demande alors la date, proposée à son entrée).
const debutAnnee = () => `${aujourdhuiIso().slice(0, 4)}-01-01`
const dateEntreeTardive = () => {
  const entree = props.titulaire?.date_entree
  return entree && entree > debutAnnee() ? entree : null
}

const choisir = () => {
  choixOuvert.value = false
  const trame = trameCourante.value
  if (trame) {
    dateDebut.value = trame.date_debut
    edition.value = versEdition(trame.horaires)
  } else {
    demanderDate.value = !!dateEntreeTardive()
    dateDebut.value = dateEntreeTardive() || debutAnnee()
  }
}

// Planning en vigueur aujourd'hui (les trames sont triées de la plus récente à la plus ancienne), sinon le plus ancien.
const trameEnVigueur = (liste) => liste.find((t) => t.date_debut <= aujourdhuiIso()) ?? liste[liste.length - 1]

const parametres = () => (props.titulaire?.employe_id ? { employe_id: props.titulaire.employe_id } : {})

const charger = async (idChoisi = null) => {
  trames.value = (await api.get('/planning/trames', { params: parametres() })).data.trames
  trameId.value = idChoisi ?? trameEnVigueur(trames.value)?.id ?? null
  if (!trameId.value) {
    edition.value = { 1: Array.from({ length: SAMEDI + 1 }, jourVide), 2: Array.from({ length: SAMEDI + 1 }, jourVide) }
  }
  choisir()
}

watch(() => props.titulaire, async (titulaire) => {
  erreur.value = message.value = ''
  if (!titulaire) return
  try {
    await charger()
  } catch (error) {
    erreur.value = await messageErreur(error)
  }
})

const copierSemaine = () => {
  edition.value['2'] = edition.value['1'].map((jour) => ({ matin: [...jour.matin], apres_midi: [...jour.apres_midi] }))
}

const executer = async (action, succes) => {
  erreur.value = message.value = ''
  enCours.value = true
  try {
    await action()
    message.value = succes
    emit('modifie')
    return true
  } catch (error) {
    erreur.value = await messageErreur(error)
    return false
  } finally {
    enCours.value = false
  }
}

// Avec un planning existant, on demande d'abord s'il s'agit d'une correction ou d'un changement à partir d'une date.
const valider = () => {
  if (trameId.value && !choixOuvert.value) {
    mode.value = 'corriger'
    dateDebut.value = aujourdhuiIso()
    choixOuvert.value = true
    return
  }
  enregistrer()
}

const enregistrer = async () => {
  const corriger = !!trameId.value && mode.value === 'corriger'
  const reussi = await executer(async () => {
    const horaires = versApi()
    const { data } = corriger
      ? await api.put(`/planning/trames/${trameId.value}`, { date_debut: trameCourante.value.date_debut, horaires })
      : await api.post('/planning/trames', { date_debut: dateDebut.value, horaires, ...parametres() })
    await charger(data.id)
  }, 'Planning enregistré.')
  if (reussi) emit('fermer')
}

const supprimer = () => {
  if (!confirm('Supprimer ce planning ? Les semaines concernées reprendront le planning précédent (ou aucun).')) return
  executer(async () => {
    await api.delete(`/planning/trames/${trameId.value}`)
    await charger()
  }, 'Planning supprimé.')
}
</script>
