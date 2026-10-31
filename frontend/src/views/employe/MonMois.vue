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
            :deplacement-modifiable="(d) => deplacementModifiableParEmploye(d.date)"
            :jours-fermeture="joursFermeture"
            :contrats="employe.contrats"
            @choisir-jour="nouveauDeplacement"
            @modifier-deplacement="modifierDeplacement"
          />
        </div>
        <div v-if="info" class="alert alert-info py-2 small mt-2 mb-0" role="status">{{ info }}</div>
        <p class="text-muted small mt-2">
          <i class="bi bi-car-front"></i> Pour déclarer un déplacement professionnel, cliquez sur la date ; pour le corriger ou le supprimer,
          cliquez sur le crayon. Possible pour le mois en cours, et pour le mois précédent jusqu'au {{ JOUR_LIMITE_MOIS_PRECEDENT }} inclus.
          Les heures et les absences sont saisies par la pharmacienne : si quelque chose vous semble inexact, parlez-lui en.
        </p>
      </div>
      <div class="col-xl-3 d-flex flex-column gap-3">
        <ResumeMois :employe="employe" :mois="mois" />
      </div>
    </div>

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
import MoisNavigateur from '../../components/MoisNavigateur.vue'
import ResumeMois from '../../components/ResumeMois.vue'
import { useMoisUrl } from '../../composables/useMoisUrl'
import api, { messageErreur } from '../../services/api'
import { JOUR_LIMITE_MOIS_PRECEDENT, absenceBloquanteDuJour, deplacementModifiableParEmploye } from '../../utils/dates'

const mois = useMoisUrl()
const donnees = ref(null)
const erreur = ref('')
const info = ref('')

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

const nouveauDeplacement = (jour) => {
  info.value = ''
  if (!deplacementModifiableParEmploye(jour)) {
    info.value = `Ce mois est clôturé pour la saisie des déplacements. Pour un oubli, adressez-vous à la pharmacienne.`
    return
  }
  if (absenceBloquanteDuJour(employe.value.absences, jour)) {
    info.value = `Absent(e) ce jour-là : aucun déplacement ne peut être déclaré.`
    return
  }
  deplacementEdite.value = null
  dateChoisie.value = jour
  modalOuvert.value = true
}

const modifierDeplacement = (d) => {
  deplacementEdite.value = d
  dateChoisie.value = d.date
  modalOuvert.value = true
}

const apresEnregistrement = () => {
  modalOuvert.value = false
  charger()
}

watch(mois, () => {
  info.value = ''
  charger()
}, { immediate: true })
</script>
