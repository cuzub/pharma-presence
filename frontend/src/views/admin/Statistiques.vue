<template>
  <div>
    <div class="page-titre">
      <h1 class="h4 mb-0">Statistiques — heures en plus / en moins</h1>
      <AnneeNavigateur v-model="annee" />
    </div>
    <p class="text-muted small">
      Cumul mensuel des heures en plus (au-dessus de l’axe) et en moins (en dessous), par employé.
      Les employés partis sur l’année sont inclus, avec la mention « parti ».
    </p>

    <div v-if="erreur" class="alert alert-danger">{{ erreur }}</div>

    <div v-if="employes.length" class="carte mb-3">
      <div class="graphique-statistiques">
        <Bar :data="graphique" :options="options" />
      </div>
      <p class="text-muted small mt-2 mb-0">Cliquez sur un nom dans la légende pour masquer ou afficher un employé.</p>
    </div>

    <div class="carte p-0 table-responsive">
      <table class="table table-sm mb-0 align-middle">
        <thead>
          <tr>
            <th>Employé</th>
            <th v-for="mois in MOIS_COURTS" :key="mois" class="text-end">{{ mois }}</th>
            <th class="text-end">Total</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="chargement">
            <td :colspan="MOIS_COURTS.length + 2" class="text-center text-muted py-4">Chargement…</td>
          </tr>
          <tr v-else-if="!employes.length">
            <td :colspan="MOIS_COURTS.length + 2" class="text-center text-muted py-4">
              Aucune heure en plus ou en moins et aucun contrat en {{ annee }}.
            </td>
          </tr>
          <tr v-for="e in employes" v-else :key="e.id" data-statistiques>
            <td class="text-nowrap">
              {{ e.nom }} {{ e.prenom }}
              <span v-if="!e.actif" class="badge text-bg-secondary">parti</span>
            </td>
            <td
              v-for="(net, index) in e.net"
              :key="index"
              :class="['text-end text-nowrap', classeMinutes(net)]"
              :title="infobulle(e.plus[index], e.moins[index])"
            >{{ formatMinutes(net) }}</td>
            <td :class="['text-end text-nowrap fw-semibold col-total', classeMinutes(e.total_net)]" :title="infobulle(e.total_plus, e.total_moins)">
              {{ formatMinutes(e.total_net) }}
            </td>
          </tr>
        </tbody>
        <tfoot v-if="employes.length && !chargement">
          <tr class="table-light fw-semibold" data-equipe>
            <td>Équipe</td>
            <td
              v-for="(net, index) in totaux.net"
              :key="index"
              :class="['text-end text-nowrap', classeMinutes(net)]"
              :title="infobulle(totaux.plus[index], totaux.moins[index])"
            >{{ formatMinutes(net) }}</td>
            <td :class="['text-end text-nowrap col-total', classeMinutes(totaux.total_net)]" :title="infobulle(totaux.total_plus, totaux.total_moins)">
              {{ formatMinutes(totaux.total_net) }}
            </td>
          </tr>
        </tfoot>
      </table>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { Bar } from 'vue-chartjs'
import { BarElement, CategoryScale, Chart as ChartJS, Legend, LinearScale, Tooltip } from 'chart.js'
import AnneeNavigateur from '../../components/AnneeNavigateur.vue'
import { useAnneeUrl } from '../../composables/useAnneeUrl'
import api, { messageErreur } from '../../services/api'
import { MOIS_FR, formatMinutes } from '../../utils/dates'
import { MOIS_COURTS, jeuxGraphique } from '../../utils/statistiques'

ChartJS.register(BarElement, CategoryScale, LinearScale, Tooltip, Legend)

const annee = useAnneeUrl()
const chargement = ref(true)
const erreur = ref('')
const donnees = ref({ employes: [], totaux: { plus: [], moins: [], net: [], total_plus: 0, total_moins: 0, total_net: 0 } })
const employes = computed(() => donnees.value.employes)
const totaux = computed(() => donnees.value.totaux)

// Une seule réponse compte : la plus récente, même si l'utilisateur change d'année pendant le chargement.
let demande = 0
const charger = async () => {
  const numero = ++demande
  chargement.value = true
  erreur.value = ''
  try {
    const reponse = (await api.get(`/statistiques/${annee.value}`)).data
    if (numero === demande) donnees.value = reponse
  } catch (error) {
    if (numero === demande) erreur.value = await messageErreur(error)
  } finally {
    if (numero === demande) chargement.value = false
  }
}
watch(annee, charger, { immediate: true })

const graphique = computed(() => ({ labels: MOIS_COURTS, datasets: jeuxGraphique(employes.value) }))

// Les valeurs du graphique sont en heures ; on repasse en minutes pour l'affichage.
const minutesDuMois = (jeu, index) => Math.round((jeu?.data[index] || 0) * 60)
const moinsDuJeu = (jeu, chart) => chart.data.datasets.find((d) => d.employeId === jeu.employeId && d.sens === 'moins')

// Clic sur un employé dans la légende : masque ou affiche ses deux jeux (plus et moins).
const basculerEmploye = (_event, item, legende) => {
  const chart = legende.chart
  const jeu = chart.data.datasets[item.datasetIndex]
  const visible = !chart.isDatasetVisible(item.datasetIndex)
  chart.data.datasets.forEach((d, index) => {
    if (d.employeId === jeu.employeId) chart.setDatasetVisibility(index, visible)
  })
  chart.update()
}

const options = {
  responsive: true,
  maintainAspectRatio: false,
  scales: {
    x: { stacked: true },
    y: {
      stacked: true,
      ticks: { callback: (valeur) => formatMinutes(Math.round(valeur * 60)) || '0' }
    }
  },
  plugins: {
    legend: {
      labels: { filter: (item, data) => data.datasets[item.datasetIndex].sens === 'plus' },
      onClick: basculerEmploye
    },
    tooltip: {
      mode: 'index',
      intersect: false,
      // Une seule ligne par employé et par mois, sans employé à zéro.
      filter: (item) => item.dataset.sens === 'plus'
        && (minutesDuMois(item.dataset, item.dataIndex) !== 0 || minutesDuMois(moinsDuJeu(item.dataset, item.chart), item.dataIndex) !== 0),
      callbacks: {
        label: (item) => {
          const moins = moinsDuJeu(item.dataset, item.chart)
          const plus = minutesDuMois(item.dataset, item.dataIndex)
          const enMoins = minutesDuMois(moins, item.dataIndex)
          return `${item.dataset.label} — ${MOIS_FR[item.dataIndex]} : ${libelle(plus)} / ${libelle(enMoins)}`
        }
      }
    }
  }
}

const libelle = (minutes) => formatMinutes(minutes) || '0'
const classeMinutes = (minutes) => (minutes > 0 ? 'minutes-plus' : minutes < 0 ? 'minutes-moins' : '')
const infobulle = (plus, moins) => (plus || moins ? `En plus : ${libelle(plus)} / En moins : ${libelle(moins)}` : '')
</script>
