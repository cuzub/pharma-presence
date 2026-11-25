<template>
  <div>
    <div class="page-titre">
      <h1 class="h4 mb-0">Mon mois</h1>
      <MoisNavigateur v-model="mois" />
    </div>

    <div v-if="erreur" class="alert alert-danger">{{ erreur }}</div>

    <div v-if="employe" class="row g-3">
      <div class="col-xl-9">
        <div class="carte" data-visite="calendrier">
          <Calendrier
            :mois="mois"
            :absences="employe.absences"
            :heures="employe.heures"
            :deplacements="employe.deplacements"
            :regularisations="employe.regularisations"
            :deplacement-modifiable="(d) => saisieModifiableParEmploye(d.date)"
            :jours-fermeture="joursFermeture"
            :contrats="employe.contrats"
            :planning="employe.planning"
            :couleur="employe.couleur"
            @choisir-jour="ouvrirJour"
            @modifier-deplacement="ouvrirJour"
          />
        </div>
        <p class="text-muted small mt-2">
          <i class="bi bi-clock"></i> Pour saisir vos heures +/- ou un déplacement professionnel, cliquez sur la date.
          Possible pour le mois en cours, et pour le mois précédent jusqu'au {{ JOUR_LIMITE_MOIS_PRECEDENT }} inclus.
          Les absences sont saisies par Elise : si quelque chose vous semble inexact, parlez-lui en.
          <button type="button" class="btn btn-link btn-sm p-0 align-baseline" data-lancer-visite @click="visite.demarrer(false)">
            <i class="bi bi-compass"></i> Faire la visite guidée
          </button>
        </p>
      </div>
      <div class="col-xl-3 d-flex flex-column gap-3">
        <ResumeMois :employe="employe" :mois="mois" />
      </div>
    </div>

    <JourModal
      :ouvert="jourOuvert"
      :employe="employe"
      :jour="jourChoisi"
      vue-employe
      :jours-fermeture="joursFermeture"
      @fermer="jourOuvert = false"
      @modifie="apresModification"
    />
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import Calendrier from '../../components/Calendrier.vue'
import JourModal from '../../components/JourModal.vue'
import MoisNavigateur from '../../components/MoisNavigateur.vue'
import ResumeMois from '../../components/ResumeMois.vue'
import { useMoisUrl } from '../../composables/useMoisUrl'
import { useVisiteGuidee } from '../../composables/useVisiteGuidee'
import api, { messageErreur } from '../../services/api'
import { JOUR_LIMITE_MOIS_PRECEDENT, saisieModifiableParEmploye } from '../../utils/dates'

const visite = useVisiteGuidee()
const mois = useMoisUrl()
const donnees = ref(null)
const erreur = ref('')

const jourOuvert = ref(false)
const jourChoisi = ref('')

const employe = computed(() => donnees.value?.employes[0] || null)
const joursFermeture = computed(() => donnees.value?.jours_fermeture || [])

const charger = async () => {
  erreur.value = ''
  try {
    donnees.value = (await api.get(`/mois/${mois.value}`)).data
  } catch (error) {
    erreur.value = await messageErreur(error)
  }
}

const ouvrirJour = (jour) => {
  jourChoisi.value = jour
  jourOuvert.value = true
}

const apresModification = () => {
  jourOuvert.value = false
  charger()
}

watch(mois, charger, { immediate: true })
</script>
