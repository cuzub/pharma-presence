<template>
  <Modal :ouvert="!!titulaire" :titre="`Planning — ${titulaire?.nom || ''}`" taille="xl" @fermer="$emit('fermer')">
    <div v-if="erreur" class="alert alert-danger py-2" role="alert">{{ erreur }}</div>
    <div v-if="message" class="alert alert-success py-2" role="status">{{ message }}</div>

    <div class="d-flex flex-wrap align-items-center gap-2 mb-3">
      <button type="button" class="btn btn-outline-secondary btn-sm" title="Recopier les horaires de la semaine 1 dans la semaine 2" @click="copierSemaine">
        <i class="bi bi-copy"></i> Semaine 1 → semaine 2
      </button>
      <button type="button" class="btn btn-outline-secondary btn-sm" title="Échanger les horaires des semaines 1 et 2" @click="inverserSemaines">
        <i class="bi bi-arrow-left-right"></i> Inverser semaine 1 ↔ semaine 2
      </button>
    </div>
    <p class="form-text mt-0">
      Semaine 1 = semaines impaires, semaine 2 = semaines paires (numéro de semaine du calendrier).
      Matin de {{ PLAGES.matin[0] }} à {{ PLAGES.matin[1] }}, après-midi de {{ PLAGES.apres_midi[0] }} à {{ PLAGES.apres_midi[1] }} ;
      le samedi, le matin seulement.
    </p>

    <form id="form-trame" class="row g-3" @submit.prevent="enregistrer">
      <div v-for="semaine in ['1', '2']" :key="semaine" class="col-lg-6" :data-semaine="semaine">
        <h6 class="mb-2">Semaine {{ semaine }} <span class="text-muted small">({{ semaine === '1' ? 'impaire' : 'paire' }}) — {{ formatDuree(totalSemaine(semaine)) }}</span></h6>
        <table class="table table-sm align-middle mb-0">
          <thead>
            <tr class="small text-muted">
              <th></th>
              <th>Matin</th>
              <th>Après-midi</th>
              <th></th>
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
                  <button type="button" class="btn btn-link btn-sm p-0 text-secondary" title="Vider" :disabled="!jour[demi].some(Boolean)" :aria-label="`Vider ${JOURS_COURTS[index]} ${LIBELLES_DEMI_JOURNEE[demi]}`" @click="jour[demi] = ['', '']">
                    <i class="bi bi-x-lg"></i>
                  </button>
                </div>
                <span v-else class="small text-muted">—</span>
              </td>
              <td class="text-end">
                <button v-if="index < SAMEDI" type="button" class="btn btn-outline-secondary btn-sm py-0 px-1" :title="`Copier ces horaires sur ${JOURS_COURTS[index + 1]}`" :aria-label="`Semaine ${semaine} : copier ${JOURS_COURTS[index]} sur ${JOURS_COURTS[index + 1]}`" @click="copierJour(semaine, index)">
                  <i class="bi bi-arrow-down"></i>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </form>

    <template #footer>
      <button v-if="existe" type="button" class="btn btn-outline-danger me-auto" @click="supprimer">Supprimer ce planning</button>
      <button type="button" class="btn btn-outline-secondary" @click="$emit('fermer')">Fermer</button>
      <button type="submit" form="form-trame" class="btn btn-primary" :disabled="enCours">Enregistrer</button>
    </template>
  </Modal>
</template>

<script setup>
import { ref, watch } from 'vue'
import api, { messageErreur } from '../services/api'
import { JOURS_COURTS } from '../utils/dates'
import { DEMI_JOURNEES, LIBELLES_DEMI_JOURNEE, PLAGES, SAMEDI, formatDuree, minutesDe } from '../utils/planning'
import Modal from './Modal.vue'

// titulaire : { employe_id, nom } pour un employé, { nom } pour le planning de l'admin connecté.
const props = defineProps({ titulaire: { type: Object, default: null } })
const emit = defineEmits(['fermer', 'modifie'])

const existe = ref(false)
const edition = ref({ 1: [], 2: [] })
const erreur = ref('')
const message = ref('')
const enCours = ref(false)

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

const parametres = () => (props.titulaire?.employe_id ? { employe_id: props.titulaire.employe_id } : {})

const charger = async () => {
  const { trame } = (await api.get('/planning/trame', { params: parametres() })).data
  existe.value = !!trame
  edition.value = versEdition(trame?.horaires)
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

const inverserSemaines = () => {
  edition.value = { 1: edition.value['2'], 2: edition.value['1'] }
}

// Le samedi n'a pas d'après-midi : seul le matin du vendredi est recopié.
const copierJour = (semaine, index) => {
  const jours = edition.value[semaine]
  jours[index + 1] = {
    matin: [...jours[index].matin],
    apres_midi: index + 1 === SAMEDI ? ['', ''] : [...jours[index].apres_midi]
  }
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

const enregistrer = async () => {
  const reussi = await executer(async () => {
    await api.put('/planning/trame', { horaires: versApi(), ...parametres() })
    await charger()
  }, 'Planning enregistré.')
  if (reussi) emit('fermer')
}

const supprimer = () => {
  if (!confirm('Supprimer ce planning ? Plus aucun horaire habituel ne sera prévu.')) return
  executer(async () => {
    await api.delete('/planning/trame', { params: parametres() })
    await charger()
  }, 'Planning supprimé.')
}
</script>
