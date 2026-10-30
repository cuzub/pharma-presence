<template>
  <div>
    <div class="page-titre">
      <h1 class="h4 mb-0">Absences</h1>
      <button type="button" class="btn btn-primary" @click="ouvrir(null)">
        <i class="bi bi-plus-lg"></i> Nouvelle absence
      </button>
    </div>

    <div class="carte mb-3 d-flex flex-wrap gap-3 align-items-end">
      <div>
        <label for="filtre-employe" class="form-label small mb-1">Employé</label>
        <select id="filtre-employe" v-model="filtreEmploye" class="form-select form-select-sm">
          <option :value="null">Tous</option>
          <option v-for="e in referentiel.employes" :key="e.id" :value="e.id">{{ e.nom }} {{ e.prenom }}</option>
        </select>
      </div>
      <div>
        <label for="filtre-debut" class="form-label small mb-1">Depuis le</label>
        <input id="filtre-debut" v-model="filtreDebut" type="date" class="form-control form-control-sm" />
      </div>
      <div>
        <label for="filtre-fin" class="form-label small mb-1">Jusqu'au</label>
        <input id="filtre-fin" v-model="filtreFin" type="date" class="form-control form-control-sm" />
      </div>
    </div>

    <div v-if="erreur" class="alert alert-danger">{{ erreur }}</div>

    <div class="carte p-0">
      <table class="table table-hover mb-0">
        <thead>
          <tr>
            <th>Employé</th>
            <th>Motif</th>
            <th>Premier jour d'absence</th>
            <th>Jour de reprise</th>
            <th>Commentaire</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="!absences.length">
            <td colspan="6" class="text-center text-muted py-4">Aucune absence sur cette période.</td>
          </tr>
          <tr v-for="a in absences" :key="a.id">
            <td>{{ nomEmploye(a.employe_id) }}</td>
            <td><span class="pastille-motif" :style="{ background: a.motif_couleur }">{{ a.motif_libelle }}</span></td>
            <td>{{ formatFr(a.date_debut) }}</td>
            <td>
              <template v-if="a.date_reprise">{{ formatFr(a.date_reprise) }}</template>
              <span v-else class="badge text-bg-info">En cours</span>
            </td>
            <td class="small text-muted">{{ a.commentaire }}</td>
            <td class="text-end">
              <button type="button" class="btn btn-sm btn-outline-secondary" title="Modifier" @click="ouvrir(a)">
                <i class="bi bi-pencil"></i>
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <AbsenceModal
      :ouvert="modalOuvert"
      :absence="absenceEditee"
      :employe-fixe="null"
      @fermer="modalOuvert = false"
      @enregistre="apresEnregistrement"
    />
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import AbsenceModal from '../../components/AbsenceModal.vue'
import api, { messageErreur } from '../../services/api'
import { useReferentielStore } from '../../stores/referentiel'
import { ajouterJours, aujourdhuiIso, formatFr } from '../../utils/dates'

const referentiel = useReferentielStore()
const absences = ref([])
const erreur = ref('')
const filtreEmploye = ref(null)
const filtreDebut = ref(ajouterJours(aujourdhuiIso(), -90))
const filtreFin = ref('')
const modalOuvert = ref(false)
const absenceEditee = ref(null)

const nomEmploye = (id) => {
  const e = referentiel.employes.find((x) => x.id === id)
  return e ? `${e.nom} ${e.prenom}` : '—'
}

const charger = async () => {
  erreur.value = ''
  try {
    const params = { employe_id: filtreEmploye.value || undefined, debut: filtreDebut.value || undefined, fin: filtreFin.value || undefined }
    absences.value = (await api.get('/absences', { params })).data
  } catch (error) {
    erreur.value = await messageErreur(error)
  }
}

const ouvrir = (absence) => {
  absenceEditee.value = absence
  modalOuvert.value = true
}

const apresEnregistrement = () => {
  modalOuvert.value = false
  charger()
}

referentiel.chargerEmployes()
watch([filtreEmploye, filtreDebut, filtreFin], charger, { immediate: true })
</script>
