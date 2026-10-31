<template>
  <div>
    <div class="page-titre">
      <h1 class="h4 mb-0">Tableau du mois</h1>
      <MoisNavigateur v-model="mois" />
    </div>

    <div v-if="erreur" class="alert alert-danger">{{ erreur }}</div>

    <div class="carte p-0 overflow-hidden">
      <div class="table-responsive tableau-conteneur">
        <table class="table table-sm mb-0 tableau-mois">
          <thead>
            <tr>
              <th class="col-employe">Employé</th>
              <th
                v-for="jour in jours"
                :key="jour.iso"
                :class="['col-jour', jour.classes]"
                :title="jour.titre"
              >
                <div class="small text-muted">{{ jour.initiale }}</div>
                <div>{{ jour.numero }}</div>
              </th>
              <th class="col-total col-hpm" title="Solde cumulé des heures en plus / en moins à la fin du mois (tout l'historique, régularisations comprises)">H +/-</th>
              <th class="col-total col-km" title="Kilomètres de déplacements">Km</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="chargement">
              <td :colspan="jours.length + 3" class="text-center text-muted py-4">Chargement…</td>
            </tr>
            <tr v-else-if="!donnees.employes.length">
              <td :colspan="jours.length + 3" class="text-center text-muted py-4">
                Aucun employé sous contrat ce mois-ci. <RouterLink to="/employes">Ajouter un employé</RouterLink>
              </td>
            </tr>
            <tr v-for="employe in donnees.employes" :key="employe.id">
              <th class="col-employe" scope="row">
                <div class="fw-semibold text-nowrap">{{ employe.nom }} {{ employe.prenom }}</div>
                <div class="small text-muted text-nowrap">{{ texteContrat(employe) }}</div>
                <div v-for="m in employe.mouvements" :key="m" class="small text-primary text-nowrap">{{ m }}</div>
              </th>
              <td
                v-for="jour in jours"
                :key="jour.iso"
                :class="['case', jour.classes, { 'hors-contrat': horsContrat(employe, jour.iso) }]"
                :style="styleCase(employe, jour.iso)"
                :title="titreCase(employe, jour)"
                role="button"
                tabindex="0"
                :data-employe="employe.id"
                :data-jour="jour.iso"
                @click="saisie.ouvrirJour(employe.id, jour.iso)"
                @keydown.enter="saisie.ouvrirJour(employe.id, jour.iso)"
              >
                <div>
                  <span v-if="absence(employe, jour.iso)" class="code-absence">{{ absence(employe, jour.iso).motif_code }}</span>
                  <span v-else-if="employe.heures[jour.iso]" :class="['heures', employe.heures[jour.iso] < 0 ? 'minutes-moins' : 'minutes-plus']">{{ formatMinutes(employe.heures[jour.iso]) }}</span>
                </div>
                <div v-if="kmDuJour(employe, jour.iso)" class="km-jour">{{ formatNombre(kmDuJour(employe, jour.iso)) }} km</div>
                <div v-if="regularisationsDuJour(employe, jour.iso).length" class="badge regularisation regul-jour" data-regularisation>
                  {{ formatMinutes(totalRegularisationsDuJour(employe, jour.iso)) }}
                </div>
              </td>
              <td
                :class="['col-total', 'col-hpm', 'fw-semibold', employe.solde_minutes < 0 ? 'minutes-moins' : 'minutes-plus']"
                :title="titreSolde(employe)"
                data-solde
              >
                {{ formatMinutes(employe.solde_minutes) || '0' }}
              </td>
              <td class="col-total col-km">
                {{ employe.total_km ? formatNombre(employe.total_km) : '' }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="d-flex flex-wrap gap-3 mt-3 small align-items-center">
      <span class="text-muted">Légende :</span>
      <span v-for="m in referentiel.motifsActifs" :key="m.id">
        <span class="pastille-motif" :style="{ background: m.couleur }">{{ m.code }}</span> {{ m.libelle }}
      </span>
      <span><span class="legende dimanche"></span> Dimanche</span>
      <span><span class="legende ferie"></span> Férié</span>
      <span><span class="legende fermeture"></span> Fermeture</span>
      <span><span class="legende hors-contrat"></span> Hors contrat</span>
      <span><span class="badge regularisation">±h</span> Régularisation (Employés → Heures +/-)</span>
      <span class="text-muted">H +/- : solde cumulé à la fin du mois.</span>
      <span class="text-muted">Cliquez sur une case pour saisir des heures en plus / en moins, une absence ou un déplacement.</span>
    </div>

    <JourModal
      :ouvert="saisie.etat.jourOuvert"
      :employe="saisie.employeDuJour.value"
      :jour="saisie.etat.jour"
      @fermer="saisie.etat.jourOuvert = false"
      @modifie="saisie.apresModification"
      @nouvelle-absence="(jour) => saisie.nouvelleAbsence(saisie.etat.employeId, jour)"
      @modifier-absence="saisie.modifierAbsence"
      @nouveau-deplacement="(jour) => saisie.nouveauDeplacement(saisie.etat.employeId, jour)"
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
import AbsenceModal from '../../components/AbsenceModal.vue'
import DeplacementModal from '../../components/DeplacementModal.vue'
import JourModal from '../../components/JourModal.vue'
import MoisNavigateur from '../../components/MoisNavigateur.vue'
import { useMoisUrl } from '../../composables/useMoisUrl'
import { useSaisieJour } from '../../composables/useSaisieJour'
import api, { messageErreur } from '../../services/api'
import { useReferentielStore } from '../../stores/referentiel'
import { JOURS_COURTS, absenceDuJour, aujourdhuiIso, ferie, formatFr, formatMinutes, formatNombre, jourSemaine, joursDuMois, titreRegularisation } from '../../utils/dates'

const referentiel = useReferentielStore()
const mois = useMoisUrl()
const donnees = ref({ employes: [], jours_fermeture: [] })
const chargement = ref(true)
const erreur = ref('')

const charger = async () => {
  erreur.value = ''
  try {
    donnees.value = (await api.get(`/mois/${mois.value}`)).data
  } catch (error) {
    erreur.value = await messageErreur(error)
  } finally {
    chargement.value = false
  }
}

const employes = computed(() => donnees.value.employes)
const saisie = useSaisieJour({ employes, recharger: charger })

watch(mois, () => {
  chargement.value = true
  charger()
}, { immediate: true })
referentiel.chargerMotifs()

const jours = computed(() => {
  const aujourdhui = aujourdhuiIso()
  const fermetures = new Map(donnees.value.jours_fermeture.map((j) => [j.date, j.libelle || 'Fermeture']))
  return joursDuMois(mois.value).map((iso) => {
    const libelleFerie = ferie(iso)
    const fermeture = fermetures.get(iso)
    return {
      iso,
      numero: Number(iso.slice(8)),
      initiale: JOURS_COURTS[jourSemaine(iso)].slice(0, 2),
      titre: [formatFr(iso), libelleFerie, fermeture].filter(Boolean).join(' — '),
      classes: {
        dimanche: jourSemaine(iso) === 6,
        ferie: !!libelleFerie,
        fermeture: !!fermeture,
        aujourdhui: iso === aujourdhui
      }
    }
  })
})

const absence = (employe, iso) => absenceDuJour(employe.absences, iso)

const deplacementsDuJour = (employe, iso) => employe.deplacements.filter((d) => d.date === iso)
const kmDuJour = (employe, iso) => deplacementsDuJour(employe, iso).reduce((somme, d) => somme + d.km, 0)

const regularisationsDuJour = (employe, iso) => (employe.regularisations || []).filter((r) => r.jour === iso)
const totalRegularisationsDuJour = (employe, iso) =>
  regularisationsDuJour(employe, iso).reduce((somme, r) => somme + r.minutes, 0)

const titreSolde = (employe) => {
  const regularisations = (employe.regularisations || []).reduce((somme, r) => somme + r.minutes, 0)
  const morceaux = [`Solde cumulé fin de mois : ${formatMinutes(employe.solde_minutes) || '0'}`, `Net du mois : ${formatMinutes(employe.total_minutes) || '0'}`]
  if (regularisations) morceaux.push(`dont régularisations : ${formatMinutes(regularisations)}`)
  return morceaux.join(' — ')
}

const horsContrat = (employe, iso) =>
  !employe.contrats.some((c) => c.date_debut <= iso && (!c.date_fin || c.date_fin >= iso))

const styleCase = (employe, iso) => {
  const a = absence(employe, iso)
  return a ? { background: a.motif_couleur, color: '#fff' } : null
}

const titreCase = (employe, jour) => {
  const a = absence(employe, jour.iso)
  const morceaux = [`${employe.prenom} ${employe.nom}`, jour.titre]
  if (a) morceaux.push(`${a.motif_libelle}${a.date_reprise ? ` (reprise le ${formatFr(a.date_reprise)})` : ' (en cours)'}`)
  if (employe.heures[jour.iso]) morceaux.push(formatMinutes(employe.heures[jour.iso]))
  const deplacements = deplacementsDuJour(employe, jour.iso)
  if (deplacements.length) morceaux.push(`Déplacements : ${deplacements.map((d) => `${d.motif} ${formatNombre(d.km)} km`).join(', ')}`)
  morceaux.push(...regularisationsDuJour(employe, jour.iso).map(titreRegularisation))
  return morceaux.join(' — ')
}

const texteContrat = (employe) =>
  employe.contrats.map((c) => `${formatNombre(c.heures_mensuelles)} h/mois`).join(' → ') || 'Sans contrat ce mois-ci'
</script>

<style scoped>
.tableau-conteneur {
  max-height: calc(100vh - 220px);
}

/* Le tableau occupe toute la largeur de la carte ; il défile horizontalement s'il est plus large. */
.tableau-conteneur {
  width: 100%;
}

.tableau-mois {
  width: 100%;
  font-size: 0.8rem;
  border-collapse: separate;
  border-spacing: 0;
}

/* Bordures dessinées par cellule (droite et bas) : avec border-collapse, les cellules collantes décrochent au défilement. */
.tableau-mois th,
.tableau-mois td {
  border: solid #dee2e6;
  border-width: 0 1px 1px 0;
}

.tableau-mois thead th {
  position: sticky;
  top: 0;
  z-index: 2;
  background-color: #fff;
  border-top-width: 1px;
  text-align: center;
}

.col-employe {
  position: sticky;
  left: 0;
  z-index: 1;
  background-color: #fff;
  min-width: 170px;
  border-left-width: 1px !important;
  box-shadow: 2px 0 3px -2px rgba(0, 0, 0, 0.25);
}

thead .col-employe {
  z-index: 3;
}

.col-jour,
.case {
  min-width: 34px;
  text-align: center;
  padding: 2px !important;
}

.case {
  cursor: pointer;
  height: 46px;
}

.case:hover,
.case:focus {
  outline: 2px solid var(--pharma-vert);
  outline-offset: -2px;
}

.dimanche {
  background: var(--case-dimanche);
}

.ferie {
  background: var(--case-ferie);
}

.fermeture {
  background: var(--case-fermeture);
}

.case.hors-contrat {
  background: var(--case-hors-contrat);
}

thead .aujourdhui {
  color: var(--pharma-vert);
  font-weight: 700;
  border-bottom: 3px solid var(--pharma-vert);
}

.code-absence {
  font-weight: 700;
  font-size: 0.7rem;
}

.heures {
  font-weight: 700;
  font-size: 0.7rem;
  white-space: nowrap;
}

.km-jour {
  font-size: 0.65rem;
  color: #6c757d;
  white-space: nowrap;
}

.regul-jour {
  font-size: 0.6rem;
  padding: 1px 3px;
}

.col-total {
  text-align: center;
  min-width: 52px;
  white-space: nowrap;
}

/* Colonnes de totaux figées à droite : H +/- juste à gauche de Km. */
.col-km,
.col-hpm {
  position: sticky;
  z-index: 1;
  background-color: #fff;
  width: 56px;
  min-width: 56px;
  max-width: 56px;
}

.col-km {
  right: 0;
  box-shadow: -2px 0 3px -2px rgba(0, 0, 0, 0.25);
}

.col-hpm {
  right: 56px;
  box-shadow: -2px 0 3px -2px rgba(0, 0, 0, 0.25);
}

thead .col-km,
thead .col-hpm {
  z-index: 3;
}

.legende {
  display: inline-block;
  width: 14px;
  height: 14px;
  vertical-align: middle;
  border: 1px solid #ccc;
}

.legende.dimanche {
  background: var(--case-dimanche);
}

.legende.ferie {
  background: var(--case-ferie);
}

.legende.fermeture {
  background: var(--case-fermeture);
}

.legende.hors-contrat {
  background: var(--case-hors-contrat);
}
</style>
