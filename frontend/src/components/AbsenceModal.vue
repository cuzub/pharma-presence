<template>
  <Modal :ouvert="ouvert" :titre="titre" @fermer="$emit('fermer')">
    <div v-if="!enEdition">
      <p v-if="!absences.length" class="text-muted mb-0">Aucune absence enregistrée pour cet employé.</p>
      <ul v-else class="list-unstyled mb-0">
        <li v-for="a in absences" :key="a.id" class="d-flex align-items-center justify-content-between border-bottom py-2">
          <div>
            <span class="fw-semibold">{{ a.motif_libelle }}</span>
            <span class="text-muted small ms-2">{{ formatFr(a.date_debut) }} → {{ a.date_reprise ? formatFr(a.date_reprise) : 'en cours' }}</span>
          </div>
          <button type="button" class="btn btn-sm btn-secondary" aria-label="Modifier l'absence" v-infobulle="'Modifier cette absence'" @click="ouvrirEdition(a)">
            <i class="bi bi-pencil"></i>
          </button>
        </li>
      </ul>
    </div>
    <form v-else id="form-absence" @submit.prevent="enregistrer">
      <div v-if="erreur" class="alert alert-danger py-2" role="alert">
        {{ erreur }}
        <ul v-if="conflits.length" class="small mb-2 mt-1">
          <li v-for="c in conflits" :key="`${c.type}-${c.id}`">{{ jourCourt(c.jour) }} : {{ c.libelle }}</li>
        </ul>
        <button v-if="conflits.length" type="button" class="btn btn-sm btn-danger" :disabled="enCours" @click="confirmerEtEnregistrer">
          Supprimer ces saisies et enregistrer l'absence
        </button>
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
      <template v-if="!enEdition">
        <button type="button" class="btn btn-outline-secondary" @click="$emit('fermer')">Fermer</button>
        <button type="button" class="btn btn-primary" @click="ouvrirNouvelle">
          <i class="bi bi-plus-lg"></i> Nouvelle absence
        </button>
      </template>
      <template v-else>
        <button v-if="absence?.id" type="button" class="btn btn-outline-danger me-auto" :disabled="enCours" @click="supprimer">
          <i class="bi bi-trash"></i> Supprimer
        </button>
        <button type="button" class="btn btn-outline-secondary" @click="retourListe">Annuler</button>
        <button type="submit" form="form-absence" class="btn btn-primary" :disabled="enCours">Enregistrer</button>
      </template>
    </template>
  </Modal>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import api, { messageErreur } from '../services/api'
import { useReferentielStore } from '../stores/referentiel'
import { ajouterJours, formatFr } from '../utils/dates'
import Modal from './Modal.vue'

const props = defineProps({
  ouvert: { type: Boolean, default: false },
  employe: { type: Object, default: null }
})
const emit = defineEmits(['fermer', 'enregistre'])

const referentiel = useReferentielStore()
const form = reactive({ employe_id: null, motif_id: null, date_debut: '', date_reprise: '', commentaire: '' })
const absences = ref([])
const absence = ref(null)
const enEdition = ref(false)
const erreur = ref('')
const conflits = ref([])
const enCours = ref(false)

const titre = computed(() => {
  if (!enEdition.value) return `Absences — ${props.employe?.prenom ?? ''} ${props.employe?.nom ?? ''}`.trim()
  return absence.value?.id ? 'Modifier l’absence' : 'Nouvelle absence'
})

const jourCourt = (iso) => `${iso.slice(8)}/${iso.slice(5, 7)}`

const motifsProposes = computed(() =>
  referentiel.motifs.filter((m) => m.actif || m.id === absence.value?.motif_id))

const chargerAbsences = async () => {
  if (!props.employe?.id) return
  absences.value = (await api.get('/absences', { params: { employe_id: props.employe.id } })).data
}

const retourListe = () => {
  enEdition.value = false
  erreur.value = ''
  conflits.value = []
}

const remplirFormulaire = (a) => {
  absence.value = a
  Object.assign(form, {
    employe_id: props.employe?.id ?? null,
    motif_id: a?.motif_id ?? null,
    date_debut: a?.date_debut ?? '',
    date_reprise: a?.date_reprise ?? '',
    commentaire: a?.commentaire ?? ''
  })
  erreur.value = ''
  conflits.value = []
  enEdition.value = true
}

const ouvrirEdition = (a) => remplirFormulaire(a)
const ouvrirNouvelle = () => remplirFormulaire(null)

watch(() => props.ouvert, async (ouvert) => {
  if (!ouvert) return
  retourListe()
  await Promise.all([referentiel.chargerMotifs(), chargerAbsences()])
}, { immediate: true })

const envoyer = async (confirmerSuppression) => {
  erreur.value = ''
  conflits.value = []
  enCours.value = true
  const payload = { ...form, date_reprise: form.date_reprise || null, confirmer_suppression: confirmerSuppression }
  try {
    if (absence.value?.id) {
      await api.put(`/absences/${absence.value.id}`, payload)
    } else {
      await api.post('/absences', payload)
    }
    emit('enregistre')
    await chargerAbsences()
    retourListe()
  } catch (error) {
    const data = error?.response?.data
    if (data?.code === 'saisies_en_conflit') conflits.value = data.conflits || []
    erreur.value = await messageErreur(error)
  } finally {
    enCours.value = false
  }
}

const enregistrer = () => envoyer(false)
const confirmerEtEnregistrer = () => envoyer(true)

const supprimer = async () => {
  if (!confirm('Supprimer cette absence ?')) return
  enCours.value = true
  try {
    await api.delete(`/absences/${absence.value.id}`)
    emit('enregistre')
    await chargerAbsences()
    retourListe()
  } catch (error) {
    erreur.value = await messageErreur(error)
  } finally {
    enCours.value = false
  }
}
</script>
