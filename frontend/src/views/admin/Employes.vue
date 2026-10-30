<template>
  <div>
    <div class="page-titre">
      <h1 class="h4 mb-0">Employés</h1>
      <button type="button" class="btn btn-primary" @click="ouvrirCreation">
        <i class="bi bi-person-plus"></i> Nouvel employé
      </button>
    </div>

    <ul class="nav nav-tabs mb-3">
      <li v-for="o in onglets" :key="o.statut" class="nav-item">
        <button type="button" :class="['nav-link', { active: statut === o.statut }]" @click="statut = o.statut">{{ o.libelle }}</button>
      </li>
    </ul>

    <div v-if="erreur" class="alert alert-danger">{{ erreur }}</div>

    <div class="carte p-0">
      <table class="table table-hover mb-0">
        <thead>
          <tr>
            <th>Nom</th>
            <th>Prénom</th>
            <th>Identifiant</th>
            <th class="text-end">Contrat</th>
            <th>Entrée</th>
            <th>Sortie</th>
            <th>Compte</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="!employes.length">
            <td colspan="8" class="text-center text-muted py-4">Aucun employé.</td>
          </tr>
          <tr v-for="e in employes" :key="e.id">
            <td class="fw-semibold">{{ e.nom }}</td>
            <td>{{ e.prenom }}</td>
            <td><code>{{ e.identifiant }}</code></td>
            <td class="text-end">{{ formatNombre(e.heures_mensuelles) }} h/mois</td>
            <td>{{ formatFr(e.date_entree) }}</td>
            <td>{{ formatFr(e.date_sortie) }}</td>
            <td>
              <span :class="['badge', e.actif ? 'text-bg-success' : 'text-bg-secondary']">{{ e.actif ? 'Actif' : 'Désactivé' }}</span>
            </td>
            <td class="text-end">
              <button type="button" class="btn btn-sm btn-outline-primary" @click="ficheId = e.id">
                <i class="bi bi-person-gear"></i> Gérer
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <Modal :ouvert="creationOuverte" titre="Arrivée d'un nouvel employé" @fermer="creationOuverte = false">
      <form id="form-creation" @submit.prevent="creer">
        <div v-if="erreurCreation" class="alert alert-danger py-2">{{ erreurCreation }}</div>
        <div class="row g-3">
          <div class="col-sm-6">
            <label for="c-nom" class="form-label">Nom</label>
            <input id="c-nom" v-model.trim="creation.nom" class="form-control" required maxlength="100" @input="suggererIdentifiant" />
          </div>
          <div class="col-sm-6">
            <label for="c-prenom" class="form-label">Prénom</label>
            <input id="c-prenom" v-model.trim="creation.prenom" class="form-control" required maxlength="100" @input="suggererIdentifiant" />
          </div>
          <div class="col-sm-6">
            <label for="c-entree" class="form-label">Date d'entrée</label>
            <input id="c-entree" v-model="creation.date_entree" type="date" class="form-control" required />
          </div>
          <div class="col-sm-6">
            <label for="c-heures" class="form-label">Contrat (heures / mois)</label>
            <input id="c-heures" v-model="creation.heures_mensuelles" type="number" min="1" step="0.01" class="form-control" required placeholder="151,67" />
          </div>
          <div class="col-sm-6">
            <label for="c-identifiant" class="form-label">Identifiant de connexion</label>
            <input id="c-identifiant" v-model.trim="creation.identifiant" class="form-control" required pattern="[a-z0-9][a-z0-9._\-]{2,39}" @input="identifiantModifie = true" />
            <div class="form-text">Minuscules, chiffres, point ou tiret.</div>
          </div>
          <div class="col-sm-6">
            <label for="c-mdp" class="form-label">Mot de passe provisoire</label>
            <div class="input-group">
              <input id="c-mdp" v-model="creation.mot_de_passe_provisoire" class="form-control font-monospace" required :minlength="LONGUEUR_MIN_MDP" />
              <button type="button" class="btn btn-outline-secondary" title="Générer" @click="creation.mot_de_passe_provisoire = genererMotDePasse()">
                <i class="bi bi-arrow-repeat"></i>
              </button>
            </div>
            <div class="form-text">À transmettre à l'employé ; il devra le changer à sa première connexion.</div>
          </div>
        </div>
      </form>
      <template #footer>
        <button type="button" class="btn btn-outline-secondary" @click="creationOuverte = false">Annuler</button>
        <button type="submit" form="form-creation" class="btn btn-primary">Créer l'employé et son compte</button>
      </template>
    </Modal>

    <Modal :ouvert="!!identifiantsCrees" titre="Compte créé" @fermer="identifiantsCrees = null">
      <p>Transmettez ces informations à <strong>{{ identifiantsCrees?.nom }}</strong> :</p>
      <dl class="row mb-0">
        <dt class="col-5">Adresse</dt>
        <dd class="col-7"><code>{{ adresseApplication }}</code></dd>
        <dt class="col-5">Identifiant</dt>
        <dd class="col-7"><code>{{ identifiantsCrees?.identifiant }}</code></dd>
        <dt class="col-5">Mot de passe provisoire</dt>
        <dd class="col-7"><code>{{ identifiantsCrees?.motDePasse }}</code></dd>
      </dl>
      <p class="small text-muted mt-3 mb-0">Ce mot de passe ne sera plus affiché. En cas d'oubli, vous pourrez en définir un nouveau.</p>
    </Modal>

    <FicheEmploye :employe-id="ficheId" @fermer="ficheId = null" @modifie="charger" />
  </div>
</template>

<script setup>
import { reactive, ref, watch } from 'vue'
import FicheEmploye from '../../components/FicheEmploye.vue'
import Modal from '../../components/Modal.vue'
import api, { messageErreur } from '../../services/api'
import { useReferentielStore } from '../../stores/referentiel'
import { aujourdhuiIso, formatFr, formatNombre } from '../../utils/dates'
import { LONGUEUR_MIN_MDP, genererMotDePasse } from '../../utils/motDePasse'

const referentiel = useReferentielStore()
const onglets = [
  { statut: 'actifs', libelle: 'En poste' },
  { statut: 'partis', libelle: 'Partis' },
  { statut: 'tous', libelle: 'Tous' }
]
const statut = ref('actifs')
const employes = ref([])
const erreur = ref('')
const ficheId = ref(null)
const creationOuverte = ref(false)
const erreurCreation = ref('')
const identifiantModifie = ref(false)
const identifiantsCrees = ref(null)
const creation = reactive({})
const adresseApplication = window.location.origin

const charger = async () => {
  erreur.value = ''
  try {
    employes.value = (await api.get('/employes', { params: { statut: statut.value } })).data
    referentiel.chargerEmployes()
  } catch (error) {
    erreur.value = await messageErreur(error)
  }
}

const normaliser = (texte) => texte.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '')

const suggererIdentifiant = () => {
  if (identifiantModifie.value) return
  creation.identifiant = [normaliser(creation.prenom || ''), normaliser(creation.nom || '')].filter(Boolean).join('.')
}

const ouvrirCreation = () => {
  Object.assign(creation, {
    nom: '', prenom: '', identifiant: '', date_entree: aujourdhuiIso(), heures_mensuelles: '', mot_de_passe_provisoire: genererMotDePasse()
  })
  identifiantModifie.value = false
  erreurCreation.value = ''
  creationOuverte.value = true
}

const creer = async () => {
  erreurCreation.value = ''
  try {
    const fiche = (await api.post('/employes', creation)).data
    creationOuverte.value = false
    identifiantsCrees.value = { nom: `${fiche.prenom} ${fiche.nom}`, identifiant: fiche.identifiant, motDePasse: creation.mot_de_passe_provisoire }
    await charger()
  } catch (error) {
    erreurCreation.value = await messageErreur(error)
  }
}

watch(statut, charger, { immediate: true })
</script>
