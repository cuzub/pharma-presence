<template>
  <Modal :ouvert="!!employe" :titre="employe ? `Heures +/- — ${employe.prenom} ${employe.nom}` : ''" taille="lg" @fermer="$emit('fermer')">
    <template v-if="employe">
      <div class="solde-carte mb-3" data-solde-heures>
        <div class="small text-muted">Solde à ce jour</div>
        <div :class="['solde-valeur', classe(solde)]">{{ libelle(solde) }}</div>
        <div class="small text-muted">Heures +/- saisies au jour le jour et régularisations, depuis le début.</div>
      </div>

      <div v-if="erreur" class="alert alert-danger py-2 small" role="alert">{{ erreur }}</div>

      <form class="border rounded p-3 mb-4" data-form-regularisation @submit.prevent="enregistrer">
        <h6 class="mb-3">
          <template v-if="editee">Modifier l'opération du {{ formatFr(editee.jour) }}</template>
          <template v-else>Nouvelle opération</template>
        </h6>

        <div class="mb-3">
          <div class="form-label small mb-1">Motif</div>
          <div class="d-flex flex-wrap gap-2" role="group" aria-label="Motif">
            <button
              v-for="m in MOTIFS"
              :key="m.cle"
              type="button"
              :class="['btn btn-sm', form.motif === m.cle ? 'btn-secondary' : 'btn-outline-secondary']"
              :aria-pressed="form.motif === m.cle"
              @click="choisirMotif(m)"
            >
              <i :class="['bi', m.icone]"></i> {{ m.libelle }}
            </button>
          </div>
        </div>

        <div class="mb-3">
          <div class="form-label small mb-1">Opération</div>
          <div class="btn-group w-100" role="group" aria-label="Opération">
            <button
              type="button"
              :class="['btn', form.sens === 'credit' ? 'btn-success' : 'btn-outline-success']"
              :aria-pressed="form.sens === 'credit'"
              data-sens="credit"
              @click="form.sens = 'credit'"
            >
              <i class="bi bi-plus-circle"></i> Ajouter au compteur
            </button>
            <button
              type="button"
              :class="['btn', form.sens === 'debit' ? 'btn-warning' : 'btn-outline-warning']"
              :aria-pressed="form.sens === 'debit'"
              data-sens="debit"
              @click="form.sens = 'debit'"
            >
              <i class="bi bi-dash-circle"></i> Retirer du compteur
            </button>
          </div>
        </div>

        <div class="row g-2 mb-3">
          <div class="col-6 col-sm-3">
            <label for="hpm-heures" class="form-label small mb-1">Heures</label>
            <input id="hpm-heures" v-model="form.heures" type="number" min="0" max="500" step="1" class="form-control" placeholder="0" />
          </div>
          <div class="col-6 col-sm-3">
            <label for="hpm-minutes" class="form-label small mb-1">Minutes</label>
            <select id="hpm-minutes" v-model.number="form.minutes" class="form-select">
              <option v-for="m in MINUTES" :key="m" :value="m">{{ String(m).padStart(2, '0') }}</option>
            </select>
          </div>
          <div class="col-sm-6">
            <label for="hpm-jour" class="form-label small mb-1">Date</label>
            <input id="hpm-jour" v-model="form.jour" type="date" class="form-control" required />
          </div>
        </div>

        <div class="mb-3">
          <label for="hpm-commentaire" class="form-label small mb-1">Commentaire <span class="text-muted">(facultatif)</span></label>
          <input id="hpm-commentaire" v-model.trim="form.commentaire" maxlength="200" class="form-control" placeholder="Ex. : heures payées sur la paie d'octobre" />
        </div>

        <div class="d-flex flex-wrap align-items-center gap-2">
          <div class="me-auto small" data-apercu>
            <template v-if="minutes !== null">
              Solde : <span :class="classe(soldeAvant)">{{ libelle(soldeAvant) }}</span>
              <i class="bi bi-arrow-right mx-1"></i>
              <strong :class="classe(soldeApres)">{{ libelle(soldeApres) }}</strong>
            </template>
            <span v-else class="text-muted">Indiquez une durée.</span>
          </div>
          <button v-if="editee" type="button" class="btn btn-outline-secondary" @click="reinitialiser">Annuler</button>
          <button type="submit" class="btn btn-primary" :disabled="enCours || minutes === null">
            {{ editee ? 'Enregistrer la modification' : 'Enregistrer' }}
          </button>
        </div>
      </form>

      <h6>Historique des régularisations</h6>
      <table v-if="regularisations.length" class="table table-sm align-middle mb-0">
        <thead>
          <tr>
            <th>Date</th>
            <th class="text-end">Heures</th>
            <th>Commentaire</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in regularisations" :key="r.id" :class="{ 'table-active': editee?.id === r.id }" data-regularisation>
            <td class="text-nowrap">{{ formatFr(r.jour) }}</td>
            <td class="text-end"><span class="badge regularisation">{{ formatMinutes(r.minutes) }}</span></td>
            <td class="w-100">{{ r.commentaire }}</td>
            <td class="text-nowrap text-end">
              <button type="button" class="btn btn-sm btn-outline-secondary" title="Modifier" :aria-label="`Modifier la régularisation du ${formatFr(r.jour)}`" @click="editer(r)">
                <i class="bi bi-pencil"></i>
              </button>
              <button type="button" class="btn btn-sm btn-outline-danger ms-1" title="Supprimer" :aria-label="`Supprimer la régularisation du ${formatFr(r.jour)}`" @click="supprimer(r)">
                <i class="bi bi-trash"></i>
              </button>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-else class="text-muted small mb-0">Aucune régularisation pour l'instant.</p>
      <p class="form-text mb-0 mt-2">
        Les régularisations apparaissent en violet dans le tableau du mois et le calendrier de l'employé, et comptent
        dans le solde et les statistiques (pas dans l'export pour le comptable).
      </p>
    </template>
  </Modal>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import api, { messageErreur } from '../services/api'
import { aujourdhuiIso, formatFr, formatMinutes, minutesRegularisation } from '../utils/dates'
import Modal from './Modal.vue'

const MOTIFS = [
  { cle: 'payees', libelle: 'Heures payées', icone: 'bi-cash-coin', sens: 'debit', commentaire: 'Heures payées sur la paie' },
  { cle: 'recup', libelle: 'Récupération', icone: 'bi-cup-hot', sens: 'debit', commentaire: 'Récupération' },
  { cle: 'depart', libelle: 'Solde de départ', icone: 'bi-flag', sens: 'credit', commentaire: "Solde de départ (avant l'outil)" },
  { cle: 'correction', libelle: 'Correction', icone: 'bi-pencil', sens: null, commentaire: 'Correction' }
]
const MINUTES = Array.from({ length: 12 }, (_, i) => i * 5)

const props = defineProps({ employe: { type: Object, default: null } })
const emit = defineEmits(['fermer', 'modifie'])

const regularisations = ref([])
const solde = ref(0)
const erreur = ref('')
const enCours = ref(false)
const editee = ref(null)
const form = reactive({})

const reinitialiser = () => {
  editee.value = null
  Object.assign(form, { motif: null, sens: 'credit', heures: '', minutes: 0, jour: aujourdhuiIso(), commentaire: '' })
}
reinitialiser()

const minutes = computed(() => minutesRegularisation(form.sens, form.heures, form.minutes))
// En modification, l'ancienne valeur est retirée du solde avant d'appliquer la nouvelle.
const soldeAvant = computed(() => solde.value)
const soldeApres = computed(() => solde.value - (editee.value?.minutes || 0) + (minutes.value || 0))

const libelle = (m) => formatMinutes(m) || '0'
const classe = (m) => (m < 0 ? 'minutes-moins' : m > 0 ? 'minutes-plus' : '')

const charger = async () => {
  try {
    const donnees = (await api.get(`/employes/${props.employe.id}/regularisations`)).data
    regularisations.value = donnees.regularisations
    solde.value = donnees.solde_minutes
  } catch (error) {
    erreur.value = await messageErreur(error)
  }
}

watch(() => props.employe?.id, (id) => {
  erreur.value = ''
  regularisations.value = []
  solde.value = 0
  reinitialiser()
  if (id) charger()
}, { immediate: true })

const choisirMotif = (m) => {
  form.motif = m.cle
  if (m.sens) form.sens = m.sens
  // Le commentaire suit le motif tant qu'il n'a pas été personnalisé.
  if (!form.commentaire || MOTIFS.some((autre) => autre.commentaire === form.commentaire)) form.commentaire = m.commentaire
}

const editer = (r) => {
  erreur.value = ''
  editee.value = r
  const total = Math.abs(r.minutes)
  Object.assign(form, {
    motif: MOTIFS.find((m) => m.commentaire === r.commentaire)?.cle || null,
    sens: r.minutes < 0 ? 'debit' : 'credit',
    heures: Math.floor(total / 60) || '',
    minutes: total % 60,
    jour: r.jour,
    commentaire: r.commentaire || ''
  })
}

const enregistrer = async () => {
  erreur.value = ''
  if (minutes.value === null) {
    erreur.value = 'Indiquez une durée non nulle.'
    return
  }
  const donnees = { jour: form.jour, minutes: minutes.value, commentaire: form.commentaire }
  enCours.value = true
  try {
    if (editee.value) await api.put(`/regularisations/${editee.value.id}`, donnees)
    else await api.post(`/employes/${props.employe.id}/regularisations`, donnees)
    reinitialiser()
    await charger()
    emit('modifie')
  } catch (error) {
    erreur.value = await messageErreur(error)
  } finally {
    enCours.value = false
  }
}

const supprimer = async (r) => {
  if (!confirm(`Supprimer la régularisation de ${formatMinutes(r.minutes)} du ${formatFr(r.jour)} ?`)) return
  erreur.value = ''
  try {
    await api.delete(`/regularisations/${r.id}`)
    if (editee.value?.id === r.id) reinitialiser()
    await charger()
    emit('modifie')
  } catch (error) {
    erreur.value = await messageErreur(error)
  }
}
</script>

<style scoped>
.solde-carte {
  background: var(--regularisation-fond);
  border-left: 4px solid var(--regularisation);
  border-radius: 0.375rem;
  padding: 0.75rem 1rem;
}

.solde-valeur {
  font-size: 1.75rem;
  font-weight: 700;
  line-height: 1.2;
}
</style>
