<template>
  <div>
    <div class="page-titre">
      <h1 class="h4 mb-0">Export pour le comptable</h1>
      <MoisNavigateur v-model="mois" />
    </div>

    <div v-if="erreur" class="alert alert-danger">{{ erreur }}</div>

    <div class="carte p-0">
      <div class="table-responsive">
        <table class="table table-hover mb-0 apercu">
          <colgroup>
            <col style="width: 16%" />
            <col style="width: 14%" />
            <col style="width: 12%" />
            <col style="width: 8%" />
            <col />
          </colgroup>
          <thead>
            <tr>
              <th>Nom</th>
              <th>Prénom</th>
              <th class="text-end">Contrat</th>
              <th class="text-end">Km</th>
              <th>Périodes d'absence</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="!apercu.length">
              <td colspan="5" class="text-center text-muted py-3">Aucun employé concerné ce mois-ci.</td>
            </tr>
            <tr v-for="e in apercu" :key="e.id">
              <td class="fw-semibold">{{ e.nom.toUpperCase() }}</td>
              <td>{{ e.prenom }}</td>
              <td class="text-end text-nowrap">{{ e.contrat }}</td>
              <td class="text-end">{{ e.km }}</td>
              <td>
                <div v-for="a in e.absences" :key="a">{{ a }}</div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="carte mt-4">
      <h2 class="h6">État préparatoire</h2>
      <p class="small text-muted mb-2">
        Le fichier Excel du mois à transmettre au comptable : une ligne par employé avec son contrat,
        ses kilomètres et ses absences. Le mail pré-rempli se configure dans Paramètres.
      </p>
      <p v-if="controles?.bloquants.length" class="small text-danger">Corrigez les points bloquants pour pouvoir exporter.</p>
      <div class="d-flex flex-wrap gap-2">
        <button type="button" class="btn btn-primary" :disabled="!exportPossible" @click="exporter('etat-preparatoire.xlsx', `etat-preparatoire-${mois}.xlsx`)">
          <i class="bi bi-file-earmark-excel"></i> Télécharger État préparatoire
        </button>
        <button
          type="button"
          class="btn btn-outline-primary"
          :disabled="!exportPossible"
          v-infobulle="'Ouvre un nouveau mail pré-rempli (destinataire, titre, texte) et télécharge l\'Excel à joindre. Ces champs se configurent dans Paramètres.'"
          @click="envoyerParMail"
        >
          <i class="bi bi-envelope"></i> Envoyer par mail
        </button>
      </div>
    </div>

    <div class="carte mt-4">
      <h2 class="h6">Indemnités kilométriques (IK)</h2>
      <p class="small text-muted mb-2">
        Vos déplacements de l'année, mois par mois, avec le montant (km × coefficient IK).
        À envoyer une fois par an au comptable. Ils ne figurent pas dans l'État préparatoire.
      </p>
      <div class="d-flex flex-wrap align-items-end gap-2">
        <div>
          <label for="ik-annee" class="form-label small mb-1">Année</label>
          <select id="ik-annee" v-model.number="anneeIk" class="form-select form-select-sm">
            <option v-for="a in anneesIk" :key="a" :value="a">{{ a }}</option>
          </select>
        </div>
        <button type="button" class="btn btn-outline-primary" @click="exporterIk">
          <i class="bi bi-file-earmark-excel"></i> Télécharger mes IK
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import MoisNavigateur from '../../components/MoisNavigateur.vue'
import { useMoisUrl } from '../../composables/useMoisUrl'
import api, { messageErreur, telecharger } from '../../services/api'
import { anneeCourante, formatFr, formatNombre, libelleMois } from '../../utils/dates'

const mois = useMoisUrl()
const controles = ref(null)
const donnees = ref({ employes: [] })
const chargement = ref(true)
const erreur = ref('')
const anneeIk = ref(anneeCourante())
const anneesIk = Array.from({ length: 6 }, (_, i) => anneeCourante() - i)

const exporterIk = async () => {
  erreur.value = ''
  try {
    await telecharger(`/exports/ik/${anneeIk.value}.xlsx`, `indemnites-km-${anneeIk.value}.xlsx`)
  } catch (error) {
    erreur.value = await messageErreur(error, 'Export IK impossible')
  }
}

const exportPossible = computed(() => !chargement.value && controles.value && !controles.value.bloquants.length)

const apercu = computed(() => donnees.value.employes.map((e) => ({
  id: e.id,
  nom: e.nom,
  prenom: e.prenom,
  contrat: e.contrats.map((c) => formatNombre(c.heures_mensuelles)).join(' puis '),
  absences: e.absences.map((a) =>
    `${formatFr(a.date_debut)} → ${a.date_reprise ? `reprise ${formatFr(a.date_reprise)}` : 'en cours'} : ${a.motif_libelle}`),
  km: e.total_km ? formatNombre(e.total_km) : ''
})))

const charger = async () => {
  chargement.value = true
  erreur.value = ''
  try {
    const [c, d] = await Promise.all([api.get(`/exports/${mois.value}/controles`), api.get(`/mois/${mois.value}`)])
    controles.value = c.data
    donnees.value = d.data
  } catch (error) {
    erreur.value = await messageErreur(error)
  } finally {
    chargement.value = false
  }
}

const exporter = async (fichier, nom) => {
  erreur.value = ''
  try {
    await telecharger(`/exports/${mois.value}/${fichier}`, nom)
  } catch (error) {
    erreur.value = await messageErreur(error, 'Export impossible')
    charger()
  }
}

const DEFAUT_TITRE = 'Export {mois}'
const DEFAUT_TEXTE = "Bonjour,\n\nVeuillez trouver ci-joint l'état préparatoire de {mois}.\n\nCordialement"

const envoyerParMail = async () => {
  erreur.value = ''
  try {
    const { data: parametres } = await api.get('/parametres/mail')
    if (!parametres.destinataire) {
      erreur.value = 'Renseignez le destinataire dans Paramètres, section « Envoi de l\'export par mail ».'
      return
    }
    const libelle = libelleMois(mois.value)
    const remplacer = (texte) => texte.replaceAll('{mois}', libelle)
    const sujet = remplacer(parametres.titre || DEFAUT_TITRE)
    const texte = remplacer(parametres.texte || DEFAUT_TEXTE)
    await telecharger(`/exports/${mois.value}/etat-preparatoire.xlsx`, `etat-preparatoire-${mois.value}.xlsx`)
    window.location.href = `mailto:${encodeURIComponent(parametres.destinataire)}`
      + `?subject=${encodeURIComponent(sujet)}&body=${encodeURIComponent(texte)}`
  } catch (error) {
    erreur.value = await messageErreur(error, 'Envoi par mail impossible')
  }
}

watch(mois, charger, { immediate: true })
</script>

<style scoped>
.apercu {
  table-layout: fixed;
  width: 100%;
}
</style>
