<template>
  <div>
    <div class="page-titre">
      <h1 class="h4 mb-0">Tableau du mois</h1>
      <MoisNavigateur v-model="mois" />
    </div>

    <div v-if="erreur" class="alert alert-danger">{{ erreur }}</div>

    <div class="carte p-0 overflow-hidden">
      <div ref="conteneur" class="table-responsive tableau-conteneur">
        <table class="table table-sm mb-0 tableau-mois">
          <thead>
            <tr>
              <th class="col-employe">Employé</th>
              <template v-for="col in colonnes" :key="col.cle">
                <th
                  v-if="col.semaine"
                  class="col-semaine"
                  v-infobulle="[`Semaine ${col.numero} (semaine ${col.numero % 2 ? 1 : 2} du planning)`, 'Heures prévues au planning, du lundi au samedi', 'Absences non déduites']"
                >
                  <div class="small text-muted">S{{ col.numero }}</div>
                  <div>Total</div>
                </th>
                <th v-else :class="['col-jour', col.classes]" v-infobulle="col.lignes">
                  <div class="small text-muted">{{ col.initiale }}</div>
                  <div>{{ col.numero }}</div>
                </th>
              </template>
              <th class="col-total col-hpm" v-infobulle="['Solde H +/- cumulé à la fin du mois', 'Tout l\'historique, régularisations comprises']">H +/-</th>
              <th class="col-total col-km" v-infobulle="['Kilomètres de déplacements']">Km</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="chargement">
              <td :colspan="colonnes.length + 3" class="text-center text-muted py-4">Chargement…</td>
            </tr>
            <tr v-else-if="!donnees.employes.length">
              <td :colspan="colonnes.length + 3" class="text-center text-muted py-4">
                Aucun employé sous contrat ce mois-ci. <RouterLink to="/employes">Ajouter un employé</RouterLink>
              </td>
            </tr>
            <tr v-for="employe in donnees.employes" :key="employe.id">
              <th class="col-employe" scope="row">
                <div class="fw-semibold text-nowrap"><span class="pastille-couleur" :style="{ background: employe.couleur }"></span>{{ employe.nom }} {{ employe.prenom }}</div>
                <div class="small text-muted text-nowrap">{{ texteContrat(employe) }}</div>
                <div v-for="m in employe.mouvements" :key="m" class="small text-primary text-nowrap">{{ m }}</div>
              </th>
              <template v-for="col in colonnes" :key="col.cle">
                <td v-if="col.semaine" class="col-semaine" data-total-semaine>{{ totalSemaine(employe, col) }}</td>
                <td
                  v-else
                  :class="['case', col.classes, { 'hors-contrat': horsContrat(employe, col.iso), absent: !!absence(employe, col.iso) }]"
                  v-infobulle="titreCase(employe, col)"
                  role="button"
                  tabindex="0"
                  :data-employe="employe.id"
                  :data-jour="col.iso"
                  @click="saisie.ouvrirJour(employe.id, col.iso)"
                  @keydown.enter="saisie.ouvrirJour(employe.id, col.iso)"
                >
                  <div v-if="!absence(employe, col.iso) && !horsContrat(employe, col.iso)" :class="['planning-jour', { exception: employe.planning[col.iso]?.exception }]" data-planning>
                    <span v-for="demi in col.demis" :key="demi" class="demi" :style="styleDemi(employe, col, demi)"></span>
                  </div>
                  <div v-else-if="absence(employe, col.iso)" class="planning-jour" data-absence>
                    <span class="demi barre-absence"></span>
                  </div>
                  <div>
                    <span v-if="absence(employe, col.iso)" class="code-absence">{{ absence(employe, col.iso).motif_code }}</span>
                    <span v-else-if="employe.heures[col.iso]" :class="['heures', employe.heures[col.iso] < 0 ? 'minutes-moins' : 'minutes-plus']">{{ formatMinutes(employe.heures[col.iso]) }}</span>
                  </div>
                  <div v-if="kmDuJour(employe, col.iso)" class="km-jour">{{ formatNombre(kmDuJour(employe, col.iso)) }} km</div>
                  <div v-if="regularisationsDuJour(employe, col.iso).length" class="badge regularisation regul-jour" data-regularisation>
                    {{ formatMinutes(totalRegularisationsDuJour(employe, col.iso)) }}
                  </div>
                </td>
              </template>
              <td
                :class="['col-total', 'col-hpm', 'fw-semibold', employe.solde_minutes < 0 ? 'minutes-moins' : 'minutes-plus']"
                v-infobulle="titreSolde(employe)"
                data-solde
              >
                {{ formatMinutes(employe.solde_minutes) || '0' }}
              </td>
              <td class="col-total col-km" v-infobulle="titreKm(employe)">
                {{ employe.total_km ? formatNombre(employe.total_km) : '' }}
              </td>
            </tr>
            <tr v-if="donnees.admins?.length" class="separateur-ik">
              <th class="col-employe" scope="row">Pharmacienne (planning, IK)</th>
              <td :colspan="colonnes.length + 2"></td>
            </tr>
            <tr v-for="admin in donnees.admins" :key="'admin-' + admin.id">
              <th class="col-employe" scope="row">
                <div class="fw-semibold text-nowrap"><span class="pastille-couleur" :style="{ background: admin.couleur }"></span>{{ admin.nom }}</div>
                <div class="small text-muted text-nowrap">{{ admin.est_moi ? 'Mon planning et mes IK' : 'Lecture seule' }}</div>
              </th>
              <template v-for="col in colonnes" :key="col.cle">
                <td v-if="col.semaine" class="col-semaine" data-total-semaine>{{ totalSemaine(admin, col) }}</td>
                <td
                  v-else
                  :class="['case', col.classes, { 'lecture-seule': !admin.est_moi }]"
                  v-infobulle="titreCaseAdmin(admin, col)"
                  :role="admin.est_moi ? 'button' : null"
                  :tabindex="admin.est_moi ? 0 : null"
                  :data-admin="admin.id"
                  :data-jour="col.iso"
                  @click="admin.est_moi && ouvrirAdmin(admin, col.iso)"
                  @keydown.enter="admin.est_moi && ouvrirAdmin(admin, col.iso)"
                >
                  <div :class="['planning-jour', { exception: admin.planning[col.iso]?.exception }]" data-planning>
                    <span v-for="demi in col.demis" :key="demi" class="demi" :style="styleDemi(admin, col, demi)"></span>
                  </div>
                  <div v-if="kmDuJour(admin, col.iso)" class="km-jour">{{ formatNombre(kmDuJour(admin, col.iso)) }} km</div>
                </td>
              </template>
              <td class="col-total col-hpm"></td>
              <td class="col-total col-km" v-infobulle="titreKm(admin)">
                {{ admin.total_km ? formatNombre(admin.total_km) : '' }}
              </td>
            </tr>
            <tr v-if="!chargement && personnes.length" class="ligne-presents">
              <th class="col-employe" scope="row" v-infobulle="['Personnes prévues à la fermeture de 12h30 et de 19h30', 'Les absents ne sont pas comptés', 'Sur fond rouge : sous le seuil défini dans Paramètres']">Présents</th>
              <template v-for="col in colonnes" :key="col.cle">
                <td v-if="col.semaine" class="col-semaine"></td>
                <td v-else :class="['compte', col.classes]" :data-presents="col.iso">
                  <div v-if="!col.ferme" class="comptes-jour">
                    <span v-for="demi in col.demis" :key="demi" :class="['compte-demi', { 'sous-seuil': sousSeuil(col.iso, demi) }]" v-infobulle="titrePresents(col.iso, demi)">{{ presentsFermeture(personnes, col.iso, demi) }}</span>
                  </div>
                </td>
              </template>
              <td class="col-total col-hpm"></td>
              <td class="col-total col-km"></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="d-flex flex-wrap gap-3 mt-3 small align-items-center">
      <span class="text-muted">Légende :</span>
      <span><span class="legende absent"></span> Absence (code du motif : {{ referentiel.motifsActifs.map((m) => m.code).join(', ') }})</span>
      <span><span class="legende planning"></span> Présence prévue (matin | après-midi), à la couleur de chacun</span>
      <span><span class="legende planning exception"></span> Horaire exceptionnel</span>
      <span><span class="legende ferie"></span> Férié</span>
      <span><span class="legende fermeture"></span> Fermeture</span>
      <span><span class="legende hors-contrat"></span> Hors contrat</span>
      <span><span class="badge regularisation">±h</span> Régularisation (Employés → Heures +/-)</span>
      <span class="text-muted">Colonne « Total » : heures prévues dans la semaine (absences non déduites).</span>
      <span class="text-muted">H +/- : solde cumulé à la fin du mois.</span>
      <span class="text-muted">Dernières lignes : planning et déplacements des admins (IK, hors État préparatoire), puis le nombre de présents.</span>
      <span class="text-muted">Cliquez sur une case pour saisir des heures en plus / en moins, un déplacement ou un horaire exceptionnel.</span>
    </div>

    <JourModal
      :ouvert="saisie.etat.jourOuvert"
      :employe="saisie.employeDuJour.value"
      :jour="saisie.etat.jour"
      @fermer="saisie.etat.jourOuvert = false"
      @modifie="saisie.apresModification"
    />
    <JourModal
      ligne-admin
      :ouvert="saisieAdmin.ouvert"
      :employe="ligneAdminModal"
      :jour="saisieAdmin.jour"
      @fermer="saisieAdmin.ouvert = false"
      @modifie="apresSaisieAdmin"
    />
  </div>
</template>

<script setup>
import { computed, nextTick, reactive, ref, watch } from 'vue'
import JourModal from '../../components/JourModal.vue'
import MoisNavigateur from '../../components/MoisNavigateur.vue'
import { useMoisUrl } from '../../composables/useMoisUrl'
import { useSaisieJour } from '../../composables/useSaisieJour'
import api, { messageErreur } from '../../services/api'
import { useReferentielStore } from '../../stores/referentiel'
import { JOURS_COURTS, absenceDuJour, ajouterJours, aujourdhuiIso, ferie, formatFr, formatMinutes, formatNombre, jourSemaine, joursDuMois, titreRegularisation } from '../../utils/dates'
import { COULEUR_ABSENCE, PLAGES, demiJourneesDuJour, fondDemiJournee, formatDuree, formatHeure, lignesHoraires, numeroSemaine, presentsFermeture, sousSeuilFermeture } from '../../utils/planning'

const referentiel = useReferentielStore()
const mois = useMoisUrl()
const donnees = ref({ employes: [], admins: [], jours_fermeture: [] })
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

const seuils = ref({ seuil_semaine: null, seuil_samedi: null })
api.get('/parametres/presence').then(({ data }) => { seuils.value = data }).catch(() => {})

const conteneur = ref(null)

// Fait défiler horizontalement pour rendre visible la colonne du jour (sans bouger la page verticalement).
const defilerVersAujourdhui = () => {
  const zone = conteneur.value
  const colonne = zone?.querySelector('thead th.aujourdhui')
  if (!zone || !colonne) return
  const zoneRect = zone.getBoundingClientRect()
  const colRect = colonne.getBoundingClientRect()
  const employe = zone.querySelector('thead .col-employe')
  const gaucheVisible = zoneRect.left + (employe ? employe.getBoundingClientRect().width : 0)
  const droiteVisible = zoneRect.right
  if (colRect.left >= gaucheVisible && colRect.right <= droiteVisible) return
  const centre = (gaucheVisible + droiteVisible) / 2
  zone.scrollLeft += colRect.left + colRect.width / 2 - centre
}

watch(chargement, (enCours) => {
  if (!enCours) nextTick(defilerVersAujourdhui)
})

const jours = computed(() => {
  const aujourdhui = aujourdhuiIso()
  const fermetures = new Map(donnees.value.jours_fermeture.map((j) => [j.date, j.libelle || 'Fermeture']))
  return joursDuMois(mois.value).map((iso) => {
    const libelleFerie = ferie(iso)
    const fermeture = fermetures.get(iso)
    return {
      cle: iso,
      iso,
      numero: Number(iso.slice(8)),
      initiale: JOURS_COURTS[jourSemaine(iso)].slice(0, 2),
      lignes: [formatFr(iso), libelleFerie, fermeture].filter(Boolean),
      demis: demiJourneesDuJour(iso),
      ferme: !!libelleFerie || !!fermeture,
      classes: {
        ferie: !!libelleFerie,
        fermeture: !!fermeture,
        aujourdhui: iso === aujourdhui
      }
    }
  })
})

// La colonne du dimanche est remplacée par le total de la semaine ; une semaine qui déborde sur le mois suivant
// a son total après le dernier jour du mois.
const colonnes = computed(() => {
  const resultat = []
  const semaine = (iso) => {
    const lundi = ajouterJours(iso, -jourSemaine(iso))
    return { cle: `semaine-${lundi}`, semaine: true, lundi, numero: numeroSemaine(lundi) }
  }
  for (const jour of jours.value) {
    resultat.push(jourSemaine(jour.iso) === 6 ? semaine(jour.iso) : jour)
  }
  const dernier = jours.value[jours.value.length - 1]
  if (dernier && jourSemaine(dernier.iso) !== 6) resultat.push(semaine(dernier.iso))
  return resultat
})

const personnes = computed(() => [...donnees.value.employes, ...(donnees.value.admins || [])])

const totalSemaine = (personne, col) => formatDuree(personne.totaux_semaines?.[col.lundi] || 0)

const sousSeuil = (iso, demi) => sousSeuilFermeture(presentsFermeture(personnes.value, iso, demi), iso, seuils.value)

const titrePresents = (iso, demi) => {
  const lignes = [`${presentsFermeture(personnes.value, iso, demi)} présent(s) à la fermeture de ${formatHeure(PLAGES[demi][1])}`]
  if (sousSeuil(iso, demi)) lignes.push('Sous le seuil défini dans Paramètres')
  return lignes
}

// Jours fériés et de fermeture : la présence prévue reste visible, mais grisée.
const styleDemi = (personne, col, demi) => {
  const couleur = col.ferme ? COULEUR_ABSENCE : personne.couleur
  const fond = fondDemiJournee(personne.planning?.[col.iso]?.[demi], demi, couleur)
  return fond ? { background: fond } : null
}

const absence = (employe, iso) => absenceDuJour(employe.absences, iso)

const deplacementsDuJour = (employe, iso) => employe.deplacements.filter((d) => d.date === iso)
const kmDuJour = (employe, iso) => deplacementsDuJour(employe, iso).reduce((somme, d) => somme + d.km, 0)

const regularisationsDuJour = (employe, iso) => (employe.regularisations || []).filter((r) => r.jour === iso)
const totalRegularisationsDuJour = (employe, iso) =>
  regularisationsDuJour(employe, iso).reduce((somme, r) => somme + r.minutes, 0)

const titreSolde = (employe) => {
  const regularisations = (employe.regularisations || []).reduce((somme, r) => somme + r.minutes, 0)
  const lignes = [
    `Solde cumulé fin de mois : ${formatMinutes(employe.solde_minutes) || '0'}`,
    `Net du mois : ${formatMinutes(employe.total_minutes) || '0'}`
  ]
  if (regularisations) lignes.push(`dont régularisations : ${formatMinutes(regularisations)}`)
  return lignes
}

const titreKm = (employe) => {
  const deplacements = [...(employe.deplacements || [])].sort((a, b) => a.date.localeCompare(b.date))
  if (!deplacements.length) return ['Aucun déplacement ce mois-ci']
  return [
    `Total du mois : ${formatNombre(employe.total_km)}\u00a0km`,
    ...deplacements.map((d) => `${formatFr(d.date)}: ${d.motif} ${formatNombre(d.km)}\u00a0km`)
  ]
}

const horsContrat = (employe, iso) =>
  !employe.contrats.some((c) => c.date_debut <= iso && (!c.date_fin || c.date_fin >= iso))

const titreCase = (employe, jour) => {
  const a = absence(employe, jour.iso)
  const lignes = [`${employe.prenom} ${employe.nom}`, ...jour.lignes]
  if (a) lignes.push(`${a.motif_libelle}${a.date_reprise ? ` (reprise le ${formatFr(a.date_reprise)})` : ' (en cours)'}`)
  else lignes.push(...lignesHoraires(employe.planning?.[jour.iso]))
  if (employe.heures[jour.iso]) lignes.push(`Heures : ${formatMinutes(employe.heures[jour.iso])}`)
  const deplacements = deplacementsDuJour(employe, jour.iso)
  if (deplacements.length) {
    lignes.push('Déplacements :', ...deplacements.map((d) => `• ${d.motif} — ${formatNombre(d.km)} km`))
  }
  lignes.push(...regularisationsDuJour(employe, jour.iso).map(titreRegularisation))
  return lignes
}

const texteContrat = (employe) =>
  employe.contrats.map((c) => `${formatNombre(c.heures_mensuelles)} h/mois`).join(' → ') || 'Sans contrat ce mois-ci'

// État de saisie séparé : les ids admin sont des ids d'utilisateur, qui peuvent coïncider avec ceux des employés.
const saisieAdmin = reactive({ ouvert: false, adminId: null, jour: '' })
const ouvrirAdmin = (admin, jour) => Object.assign(saisieAdmin, { ouvert: true, adminId: admin.id, jour })
const ligneAdminModal = computed(() => {
  const admin = donnees.value.admins?.find((a) => a.id === saisieAdmin.adminId)
  return admin ? { ...admin, prenom: '', contrats: [], absences: [], heures: {}, regularisations: [] } : null
})
const apresSaisieAdmin = async () => {
  saisieAdmin.ouvert = false
  await charger()
}
const titreCaseAdmin = (admin, jour) => {
  const deplacements = deplacementsDuJour(admin, jour.iso)
  return [
    admin.nom, ...jour.lignes, ...lignesHoraires(admin.planning?.[jour.iso]),
    ...deplacements.map((d) => `• ${d.motif} — ${formatNombre(d.km)} km`)
  ]
}
</script>

<style scoped>
.tableau-conteneur {
  max-height: calc(100vh - 220px);
}

/* Barre visible qui réserve sa place : une barre superposée (macOS) masquerait la ligne « Présents » collée en bas. */
.tableau-conteneur::-webkit-scrollbar {
  width: 12px;
  height: 12px;
}

.tableau-conteneur::-webkit-scrollbar-track {
  background: #f1f3f5;
}

.tableau-conteneur::-webkit-scrollbar-thumb {
  background: #adb5bd;
  border-radius: 6px;
  border: 2px solid #f1f3f5;
}

.tableau-conteneur::-webkit-scrollbar-thumb:hover {
  background: #868e96;
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

.tableau-mois thead .col-employe {
  z-index: 3;
}

.col-jour,
.case {
  min-width: 58px;
  text-align: center;
  padding: 2px !important;
}

.case {
  cursor: pointer;
  height: 52px;
  vertical-align: top;
}

/* Bande de présence : une demi-case pour le matin, une pour l'après-midi (le samedi : le matin seul). */
.planning-jour {
  display: flex;
  gap: 2px;
  height: 12px;
  margin-bottom: 2px;
}

.planning-jour .demi {
  flex: 1;
  background: #fff;
  border: 1px solid #ced4da;
  border-radius: 2px;
}

.planning-jour.exception .demi {
  border: 1px dashed #212529;
}

.planning-jour .barre-absence,
.legende.absent {
  background: repeating-linear-gradient(-45deg, #e9ecef 0 3px, #ced4da 3px 6px);
  border-color: #adb5bd;
}

.col-semaine {
  min-width: 52px;
  text-align: center;
  font-weight: 600;
  white-space: nowrap;
  vertical-align: middle;
  background: #f1f3f5;
}

thead .col-semaine {
  background: #e9ecef;
}

.ligne-presents th,
.ligne-presents td {
  position: sticky;
  bottom: 0;
  z-index: 1;
  background: #f8f9fa;
  border-top: 2px solid #adb5bd;
  font-weight: 600;
}

.ligne-presents .col-employe,
.ligne-presents .col-km,
.ligne-presents .col-hpm {
  z-index: 2;
}

.comptes-jour {
  display: flex;
  justify-content: flex-end;
  gap: 2px;
}

/* Toujours une demi-largeur : le chiffre unique du samedi occupe la moitié droite. */
.compte-demi {
  flex: 0 0 calc(50% - 1px);
  text-align: right;
  padding: 0 3px;
  border-radius: 2px;
}

.compte-demi.sous-seuil {
  background: var(--bs-danger);
  color: #fff;
}

.case:hover,
.case:focus {
  outline: 2px solid var(--pharma-vert);
  outline-offset: -2px;
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
  color: #6c757d;
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

.tableau-mois thead .col-km,
.tableau-mois thead .col-hpm {
  z-index: 3;
}

.case.lecture-seule {
  cursor: default;
}

.case.lecture-seule:hover {
  outline: none;
}

.separateur-ik th,
.separateur-ik td {
  font-size: 0.7rem;
  text-transform: uppercase;
  color: #6c757d;
  background: #f8f9fa;
}

.legende {
  display: inline-block;
  width: 14px;
  height: 14px;
  vertical-align: middle;
  border: 1px solid #ccc;
}

.legende.absent {
  width: 28px;
}

.legende.planning {
  width: 28px;
  background: linear-gradient(to right, #fff 30%, #81c784 30%);
}

.legende.planning.exception {
  border: 1px dashed #212529;
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
