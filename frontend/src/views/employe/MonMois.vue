<template>
  <div>
    <div class="page-titre">
      <h1 class="h4 mb-0">Mon mois</h1>
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
            :deplacement-modifiable="(d) => saisieModifiableParEmploye(d.date)"
            :jours-fermeture="joursFermeture"
            :contrats="employe.contrats"
            @choisir-jour="ouvrirJour"
            @modifier-deplacement="modifierDeplacement"
          />
        </div>
        <p class="text-muted small mt-2">
          <i class="bi bi-clock"></i> Pour saisir vos heures +/- ou un déplacement professionnel, cliquez sur la date.
          Possible pour le mois en cours, et pour le mois précédent jusqu'au {{ JOUR_LIMITE_MOIS_PRECEDENT }} inclus.
          Les absences sont saisies par la pharmacienne : si quelque chose vous semble inexact, parlez-lui en.
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
      :deplacement-modifiable="(d) => saisieModifiableParEmploye(d.date)"
      @fermer="jourOuvert = false"
      @modifie="apresModification"
      @nouveau-deplacement="nouveauDeplacement"
      @modifier-deplacement="modifierDeplacement"
    />

    <DeplacementModal
      :ouvert="modalOuvert"
      :deplacement="deplacementEdite"
      :date="dateChoisie"
      @fermer="modalOuvert = false"
      @enregistre="apresEnregistrement"
    />
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import Calendrier from '../../components/Calendrier.vue'
import DeplacementModal from '../../components/DeplacementModal.vue'
import JourModal from '../../components/JourModal.vue'
import MoisNavigateur from '../../components/MoisNavigateur.vue'
import ResumeMois from '../../components/ResumeMois.vue'
import { useMoisUrl } from '../../composables/useMoisUrl'
import api, { messageErreur } from '../../services/api'
import { JOUR_LIMITE_MOIS_PRECEDENT, saisieModifiableParEmploye } from '../../utils/dates'

const mois = useMoisUrl()
const donnees = ref(null)
const erreur = ref('')

const jourOuvert = ref(false)
const jourChoisi = ref('')
const modalOuvert = ref(false)
const deplacementEdite = ref(null)
const dateChoisie = ref('')

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

const nouveauDeplacement = (jour) => {
  jourOuvert.value = false
  deplacementEdite.value = null
  dateChoisie.value = jour
  modalOuvert.value = true
}

const modifierDeplacement = (d) => {
  jourOuvert.value = false
  deplacementEdite.value = d
  dateChoisie.value = d.date
  modalOuvert.value = true
}

const apresModification = () => {
  jourOuvert.value = false
  charger()
}

const apresEnregistrement = () => {
  modalOuvert.value = false
  charger()
}

watch(mois, charger, { immediate: true })
</script>
