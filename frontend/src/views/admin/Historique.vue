<template>
  <div class="historique">
    <div class="page-titre">
      <h1 class="h4 mb-0">Historique des modifications</h1>
    </div>
    <p class="text-muted small">
      Qui a créé, modifié ou supprimé un déplacement, des heures en plus / en moins, une régularisation ou une absence, et quand.
      Cet historique ne peut être ni modifié ni effacé.
    </p>

    <form class="carte d-flex flex-wrap gap-3 align-items-end mb-3" @submit.prevent>
      <div>
        <label for="h-employe" class="form-label small mb-1">Employé</label>
        <select id="h-employe" v-model="filtres.employe_id" class="form-select form-select-sm">
          <option :value="null">Tous</option>
          <option v-for="e in referentiel.employes" :key="e.id" :value="e.id">
            {{ e.nom }} {{ e.prenom }}{{ e.actif ? '' : ' (parti)' }}
          </option>
        </select>
      </div>
      <div>
        <label for="h-mois" class="form-label small mb-1">Mois de la modification</label>
        <input id="h-mois" v-model="filtres.mois" type="month" class="form-control form-control-sm" />
      </div>
      <div>
        <label for="h-auteur" class="form-label small mb-1">Auteur</label>
        <select id="h-auteur" v-model="filtres.auteur" class="form-select form-select-sm">
          <option value="">Tous</option>
          <option value="admin">Pharmacienne</option>
          <option value="employe">Employé</option>
        </select>
      </div>
      <div>
        <label for="h-type" class="form-label small mb-1">Type</label>
        <select id="h-type" v-model="filtres.type" class="form-select form-select-sm">
          <option value="">Tous</option>
          <option v-for="(t, cle) in TYPES" :key="cle" :value="cle">{{ t.libelle }}</option>
        </select>
      </div>
      <button v-if="filtresActifs" type="button" class="btn btn-sm btn-outline-secondary" @click="reinitialiser">
        <i class="bi bi-x-lg"></i> Effacer les filtres
      </button>
    </form>

    <div v-if="erreur" class="alert alert-danger">{{ erreur }}</div>

    <div class="carte journal-carte p-0">
      <div class="table-responsive journal-defilement">
        <table class="table table-hover mb-0">
            <thead>
            <tr>
              <th>Date</th>
              <th>Auteur</th>
              <th>Employé concerné</th>
              <th>Type</th>
              <th>Action</th>
              <th>Détail</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="chargement">
              <td colspan="6" class="text-center text-muted py-4">Chargement…</td>
            </tr>
            <tr v-else-if="!resultat.lignes.length">
              <td colspan="6" class="text-center text-muted py-4">Aucune modification enregistrée.</td>
            </tr>
            <tr v-for="l in resultat.lignes" v-else :key="l.id" data-journal>
              <td class="text-nowrap small">{{ formatHorodatage(l.cree_le) }}</td>
              <td class="text-nowrap">
                {{ l.auteur_identifiant }}
              </td>
              <td class="text-nowrap">{{ l.employe_nom ? `${l.employe_nom} ${l.employe_prenom}` : l.admin_concerne_nom ? `${l.admin_concerne_nom} (IK)` : '—' }}</td>
              <td class="text-nowrap"><i :class="['bi', TYPES[l.type].icone]"></i> {{ TYPES[l.type].libelle }}</td>
              <td><span :class="['badge', ACTIONS[l.action].classe]">{{ ACTIONS[l.action].libelle }}</span></td>
              <td class="small">
                <template v-if="l.action === 'modification'">
                  <span class="text-muted text-decoration-line-through">{{ resume(l.type, l.avant) }}</span>
                  <i class="bi bi-arrow-right mx-1"></i>
                  <span>{{ resume(l.type, l.apres) }}</span>
                </template>
                <span v-else-if="l.action === 'suppression'" class="text-muted text-decoration-line-through">{{ resume(l.type, l.avant) }}</span>
                <span v-else>{{ resume(l.type, l.apres) }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <nav v-if="resultat.total > PAR_PAGE" class="d-flex justify-content-between align-items-center mt-2 small">
      <span class="text-muted">{{ premier }}–{{ dernier }} sur {{ resultat.total }}</span>
      <div class="btn-group">
        <button type="button" class="btn btn-sm btn-outline-secondary" :disabled="page === 1" @click="page--">
          <i class="bi bi-chevron-left"></i> Plus récentes
        </button>
        <button type="button" class="btn btn-sm btn-outline-secondary" :disabled="dernier >= resultat.total" @click="page++">
          Plus anciennes <i class="bi bi-chevron-right"></i>
        </button>
      </div>
    </nav>
  </div>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import api, { messageErreur } from '../../services/api'
import { useReferentielStore } from '../../stores/referentiel'
import { formatFr, formatMinutes, formatNombre } from '../../utils/dates'

const PAR_PAGE = 50

const TYPES = {
  deplacement: { libelle: 'Déplacement', icone: 'bi-car-front' },
  heures: { libelle: 'Heures +/-', icone: 'bi-clock' },
  absence: { libelle: 'Absence', icone: 'bi-calendar-x' },
  regularisation: { libelle: 'Régularisation', icone: 'bi-arrow-left-right' }
}

const ACTIONS = {
  creation: { libelle: 'Création', classe: 'text-bg-success' },
  modification: { libelle: 'Modification', classe: 'text-bg-primary' },
  suppression: { libelle: 'Suppression', classe: 'text-bg-danger' }
}

const referentiel = useReferentielStore()
const filtres = reactive({ employe_id: null, mois: '', auteur: '', type: '' })
const page = ref(1)
const resultat = ref({ total: 0, lignes: [] })
const chargement = ref(true)
const erreur = ref('')

const filtresActifs = computed(() => filtres.employe_id !== null || filtres.mois || filtres.auteur || filtres.type)
const premier = computed(() => (page.value - 1) * PAR_PAGE + 1)
const dernier = computed(() => Math.min(page.value * PAR_PAGE, resultat.value.total))

const formatHorodatage = (valeur) =>
  new Date(valeur).toLocaleString('fr-FR', { dateStyle: 'short', timeStyle: 'short' })

const resume = (type, donnees) => {
  if (!donnees) return ''
  if (type === 'deplacement') return `${formatFr(donnees.date)} : ${donnees.motif} — ${formatNombre(donnees.km)} km`
  if (type === 'heures') return `${formatFr(donnees.jour)} : ${formatMinutes(donnees.minutes)}`
  if (type === 'regularisation') {
    return `${formatFr(donnees.jour)} : ${formatMinutes(donnees.minutes)}${donnees.commentaire ? ` (${donnees.commentaire})` : ''}`
  }
  const reprise = donnees.date_reprise ? `reprise le ${formatFr(donnees.date_reprise)}` : 'en cours'
  return `${donnees.motif} du ${formatFr(donnees.date_debut)}, ${reprise}${donnees.commentaire ? ` (${donnees.commentaire})` : ''}`
}

const charger = async () => {
  chargement.value = true
  erreur.value = ''
  try {
    const params = { page: page.value, par_page: PAR_PAGE }
    for (const [cle, valeur] of Object.entries(filtres)) {
      if (valeur !== null && valeur !== '') params[cle] = valeur
    }
    resultat.value = (await api.get('/journal', { params })).data
  } catch (error) {
    erreur.value = await messageErreur(error)
  } finally {
    chargement.value = false
  }
}

const reinitialiser = () => Object.assign(filtres, { employe_id: null, mois: '', auteur: '', type: '' })

watch(filtres, () => {
  if (page.value !== 1) page.value = 1
  else charger()
})
watch(page, charger, { immediate: true })

referentiel.chargerEmployes().catch(() => {})
</script>

<style scoped>
/* La vue remplit la hauteur de l'écran (moins le padding de <main>) : seul le tableau défile. */
.historique {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 2rem);
}

.historique > * {
  flex: 0 0 auto;
}

.journal-carte {
  flex: 1 1 auto !important;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.journal-defilement {
  flex: 1 1 auto;
  min-height: 0;
  overflow: auto;
}

/* En-tête figé pendant le défilement du tableau. */
.journal-defilement thead th {
  position: sticky;
  top: 0;
  z-index: 2;
  background-color: #fff;
  box-shadow: inset 0 -1px 0 #dee2e6;
}
</style>
