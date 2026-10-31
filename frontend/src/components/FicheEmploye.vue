<template>
  <Modal :ouvert="!!employeId" :titre="fiche ? `${fiche.prenom} ${fiche.nom}` : 'Employé'" taille="lg" @fermer="$emit('fermer')">
    <div v-if="erreur" class="alert alert-danger py-2" role="alert">{{ erreur }}</div>
    <div v-if="message" class="alert alert-success py-2" role="status">
      {{ message }}
      <div v-if="motDePasseAffiche" class="mt-1">Mot de passe provisoire à transmettre : <code class="fs-6">{{ motDePasseAffiche }}</code></div>
    </div>

    <template v-if="fiche">
      <h6>Identité</h6>
      <form class="row g-2 align-items-end mb-4" @submit.prevent="enregistrerIdentite">
        <div class="col-sm-4">
          <label for="f-nom" class="form-label small mb-1">Nom</label>
          <input id="f-nom" v-model.trim="identite.nom" class="form-control form-control-sm" required />
        </div>
        <div class="col-sm-3">
          <label for="f-prenom" class="form-label small mb-1">Prénom</label>
          <input id="f-prenom" v-model.trim="identite.prenom" class="form-control form-control-sm" required />
        </div>
        <div class="col-sm-3">
          <label for="f-identifiant" class="form-label small mb-1">Identifiant</label>
          <input id="f-identifiant" v-model.trim="identite.identifiant" class="form-control form-control-sm" required />
        </div>
        <div class="col-sm-2">
          <button type="submit" class="btn btn-sm btn-outline-primary w-100">Enregistrer</button>
        </div>
      </form>

      <h6>Contrats</h6>
      <table class="table table-sm mb-2">
        <thead>
          <tr><th>Heures / mois</th><th>Début</th><th>Fin</th><th></th></tr>
        </thead>
        <tbody>
          <tr v-for="c in contratsEdites" :key="c.id">
            <td><input v-model="c.heures_mensuelles" type="number" min="1" step="0.01" class="form-control form-control-sm" aria-label="Heures par mois" /></td>
            <td><input v-model="c.date_debut" type="date" class="form-control form-control-sm" aria-label="Début" /></td>
            <td><input v-model="c.date_fin" type="date" class="form-control form-control-sm" aria-label="Fin" /></td>
            <td class="text-end text-nowrap">
              <button type="button" class="btn btn-sm btn-outline-secondary me-1" title="Enregistrer la correction" @click="corrigerContrat(c)">
                <i class="bi bi-check-lg"></i>
              </button>
              <button v-if="contratsEdites.length > 1" type="button" class="btn btn-sm btn-outline-danger" title="Supprimer" @click="supprimerContrat(c)">
                <i class="bi bi-trash"></i>
              </button>
            </td>
          </tr>
        </tbody>
      </table>
      <p class="form-text mb-4">Corrigez ici une erreur de saisie. Pour un changement de contrat, utilisez « Avenant » ci-dessous.</p>

      <RegularisationsEmploye :employe-id="employeId" @modifie="emit('modifie')" />

      <div v-if="enPoste" class="row g-3">
        <div class="col-md-4">
          <form class="border rounded p-3 h-100" @submit.prevent="avenant">
            <h6><i class="bi bi-pencil-square"></i> Avenant</h6>
            <label for="a-heures" class="form-label small mb-1">Nouvelles heures / mois</label>
            <input id="a-heures" v-model="formAvenant.heures_mensuelles" type="number" min="1" step="0.01" class="form-control form-control-sm mb-2" required />
            <label for="a-debut" class="form-label small mb-1">À partir du</label>
            <input id="a-debut" v-model="formAvenant.date_debut" type="date" class="form-control form-control-sm mb-2" required />
            <button type="submit" class="btn btn-sm btn-outline-primary w-100">Appliquer</button>
          </form>
        </div>
        <div class="col-md-4">
          <form class="border rounded p-3 h-100" @submit.prevent="depart">
            <h6><i class="bi bi-box-arrow-right"></i> Départ</h6>
            <label for="d-sortie" class="form-label small mb-1">Dernier jour sous contrat</label>
            <input id="d-sortie" v-model="formDepart.date_sortie" type="date" class="form-control form-control-sm mb-2" required />
            <p class="form-text">Le compte est désactivé immédiatement. Ses données sont conservées.</p>
            <button type="submit" class="btn btn-sm btn-outline-danger w-100">Enregistrer le départ</button>
          </form>
        </div>
        <div class="col-md-4">
          <div class="border rounded p-3 h-100">
            <h6><i class="bi bi-key"></i> Mot de passe oublié</h6>
            <p class="form-text">Génère un nouveau mot de passe provisoire, à changer à la prochaine connexion.</p>
            <button type="button" class="btn btn-sm btn-outline-secondary w-100" :disabled="!fiche.actif" @click="reinitialiser">
              Nouveau mot de passe provisoire
            </button>
          </div>
        </div>
      </div>

      <form v-else class="border rounded p-3" @submit.prevent="retour">
        <h6><i class="bi bi-arrow-return-left"></i> Retour de l'employé</h6>
        <div class="row g-2 align-items-end">
          <div class="col-sm-4">
            <label for="r-entree" class="form-label small mb-1">Date de retour</label>
            <input id="r-entree" v-model="formRetour.date_entree" type="date" class="form-control form-control-sm" required />
          </div>
          <div class="col-sm-4">
            <label for="r-heures" class="form-label small mb-1">Contrat (heures / mois)</label>
            <input id="r-heures" v-model="formRetour.heures_mensuelles" type="number" min="1" step="0.01" class="form-control form-control-sm" required />
          </div>
          <div class="col-sm-4">
            <button type="submit" class="btn btn-sm btn-primary w-100">Réactiver le compte</button>
          </div>
        </div>
      </form>
    </template>
  </Modal>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import api, { messageErreur } from '../services/api'
import { aujourdhuiIso } from '../utils/dates'
import { genererMotDePasse } from '../utils/motDePasse'
import Modal from './Modal.vue'
import RegularisationsEmploye from './RegularisationsEmploye.vue'

const props = defineProps({ employeId: { type: Number, default: null } })
const emit = defineEmits(['fermer', 'modifie'])

const fiche = ref(null)
const erreur = ref('')
const message = ref('')
const motDePasseAffiche = ref('')
const identite = reactive({ nom: '', prenom: '', identifiant: '' })
const contratsEdites = ref([])
const formAvenant = reactive({ heures_mensuelles: '', date_debut: '' })
const formDepart = reactive({ date_sortie: '' })
const formRetour = reactive({ date_entree: '', heures_mensuelles: '' })

const enPoste = computed(() => fiche.value?.contrats.some((c) => !c.date_fin))

const appliquer = (donnees) => {
  fiche.value = donnees
  Object.assign(identite, { nom: donnees.nom, prenom: donnees.prenom, identifiant: donnees.identifiant })
  contratsEdites.value = donnees.contrats.map((c) => ({ ...c, date_fin: c.date_fin || '' }))
  const dernier = donnees.contrats[donnees.contrats.length - 1]
  Object.assign(formAvenant, { heures_mensuelles: dernier?.heures_mensuelles ?? '', date_debut: '' })
  Object.assign(formDepart, { date_sortie: aujourdhuiIso() })
  Object.assign(formRetour, { date_entree: aujourdhuiIso(), heures_mensuelles: dernier?.heures_mensuelles ?? '' })
}

watch(() => props.employeId, async (id) => {
  fiche.value = null
  erreur.value = message.value = motDePasseAffiche.value = ''
  if (!id) return
  try {
    appliquer((await api.get(`/employes/${id}`)).data)
  } catch (error) {
    erreur.value = await messageErreur(error)
  }
})

const executer = async (requete, succes, motDePasse = '') => {
  erreur.value = message.value = motDePasseAffiche.value = ''
  try {
    const reponse = await requete()
    if (reponse.data?.contrats) appliquer(reponse.data)
    message.value = succes
    motDePasseAffiche.value = motDePasse
    emit('modifie')
  } catch (error) {
    erreur.value = await messageErreur(error)
  }
}

const url = () => `/employes/${props.employeId}`

const enregistrerIdentite = () => executer(() => api.put(url(), identite), 'Identité enregistrée.')

const corrigerContrat = (c) => executer(
  () => api.put(`${url()}/contrats/${c.id}`, { heures_mensuelles: c.heures_mensuelles, date_debut: c.date_debut, date_fin: c.date_fin || null }),
  'Contrat corrigé.'
)

const supprimerContrat = (c) => {
  if (confirm('Supprimer ce contrat ?')) executer(() => api.delete(`${url()}/contrats/${c.id}`), 'Contrat supprimé.')
}

const avenant = () => executer(() => api.post(`${url()}/contrats`, formAvenant), 'Avenant enregistré.')

const depart = () => {
  if (confirm(`Enregistrer le départ de ${fiche.value.prenom} ${fiche.value.nom} ? Son compte sera désactivé immédiatement.`)) {
    executer(() => api.post(`${url()}/depart`, formDepart), 'Départ enregistré, compte désactivé.')
  }
}

const retour = () => {
  const motDePasse = genererMotDePasse()
  executer(
    () => api.post(`${url()}/retour`, { ...formRetour, mot_de_passe_provisoire: motDePasse }),
    'Retour enregistré, compte réactivé.',
    motDePasse
  )
}

const reinitialiser = () => {
  const motDePasse = genererMotDePasse()
  executer(
    () => api.post(`${url()}/mot-de-passe`, { mot_de_passe_provisoire: motDePasse }),
    'Nouveau mot de passe provisoire défini.',
    motDePasse
  )
}
</script>
