<template>
  <div>
    <div class="page-titre">
      <div class="d-flex align-items-center gap-3 flex-wrap">
        <h1 class="h4 mb-0">Calendrier</h1>
        <select v-model="employeId" class="form-select form-select-sm w-auto" aria-label="Employé">
          <option :value="null" disabled>Choisir un employé…</option>
          <option v-for="e in referentiel.employes" :key="e.id" :value="e.id">
            {{ e.nom }} {{ e.prenom }}{{ e.actif ? '' : ' (parti)' }}
          </option>
        </select>
      </div>
      <MoisNavigateur v-model="mois" />
    </div>

    <div v-if="erreur" class="alert alert-danger">{{ erreur }}</div>

    <div v-if="employe" class="row g-3">
      <div class="col-xl-9">
        <div class="carte">
          <Calendrier
            :mois="mois"
            :absences="employe.absences"
            :heures="employe.heures"
            :deplacements="employe.deplacements"
            :jours-fermeture="joursFermeture"
            :contrats="employe.contrats"
            @choisir-jour="(jour) => saisie.ouvrirJour(employe.id, jour)"
            @modifier-deplacement="saisie.modifierDeplacement"
          />
        </div>
      </div>
      <div class="col-xl-3">
        <ResumeMois :employe="employe" :mois="mois" />
      </div>
    </div>
    <p v-else-if="!employeId" class="text-muted">Choisissez un employé pour afficher et modifier son calendrier.</p>

    <JourModal
      :ouvert="saisie.etat.jourOuvert"
      :employe="employe"
      :jour="saisie.etat.jour"
      @fermer="saisie.etat.jourOuvert = false"
      @modifie="saisie.apresModification"
      @nouvelle-absence="(jour) => saisie.nouvelleAbsence(employe.id, jour)"
      @modifier-absence="saisie.modifierAbsence"
      @nouveau-deplacement="(jour) => saisie.nouveauDeplacement(employe.id, jour)"
      @modifier-deplacement="saisie.modifierDeplacement"
    />
    <AbsenceModal
      :ouvert="saisie.etat.absenceOuverte"
      :absence="saisie.etat.absence"
      :employe-fixe="saisie.etat.absenceEmployeId"
      :date-debut="saisie.etat.absenceDebut"
      @fermer="saisie.etat.absenceOuverte = false"
      @enregistre="saisie.apresModification"
    />
    <DeplacementModal
      :ouvert="saisie.etat.deplacementOuvert"
      :deplacement="saisie.etat.deplacement"
      :employe-id="saisie.etat.deplacementEmployeId"
      :date="saisie.etat.deplacementDate"
      @fermer="saisie.etat.deplacementOuvert = false"
      @enregistre="saisie.apresModification"
    />
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AbsenceModal from '../../components/AbsenceModal.vue'
import Calendrier from '../../components/Calendrier.vue'
import DeplacementModal from '../../components/DeplacementModal.vue'
import JourModal from '../../components/JourModal.vue'
import MoisNavigateur from '../../components/MoisNavigateur.vue'
import ResumeMois from '../../components/ResumeMois.vue'
import { useMoisUrl } from '../../composables/useMoisUrl'
import { useSaisieJour } from '../../composables/useSaisieJour'
import api, { messageErreur } from '../../services/api'
import { useReferentielStore } from '../../stores/referentiel'

const route = useRoute()
const router = useRouter()
const referentiel = useReferentielStore()
const mois = useMoisUrl()
const donnees = ref({ employes: [], jours_fermeture: [] })
const erreur = ref('')

const employeId = computed({
  get: () => (route.query.employe ? Number(route.query.employe) : null),
  set: (id) => router.replace({ query: { ...route.query, employe: id } })
})

const joursFermeture = computed(() => donnees.value.jours_fermeture)
const employe = computed(() => {
  if (!employeId.value) return null
  const trouve = donnees.value.employes.find((e) => e.id === employeId.value)
  if (trouve) return trouve
  const fiche = referentiel.employes.find((e) => e.id === employeId.value)
  return fiche ? { ...fiche, contrats: [], absences: [], heures: {}, deplacements: [], total_minutes: 0, total_km: 0, mouvements: [] } : null
})

const charger = async () => {
  erreur.value = ''
  try {
    donnees.value = (await api.get(`/mois/${mois.value}`)).data
  } catch (error) {
    erreur.value = await messageErreur(error)
  }
}

const saisie = useSaisieJour({ employes: computed(() => (employe.value ? [employe.value] : [])), recharger: charger })

referentiel.chargerEmployes().then((liste) => {
  if (!employeId.value && liste.length) employeId.value = liste.find((e) => e.actif)?.id ?? liste[0].id
})
watch(mois, charger, { immediate: true })
</script>
