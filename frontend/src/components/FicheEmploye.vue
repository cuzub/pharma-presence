<template>
  <Modal :ouvert="!!employeId" :titre="fiche ? `${fiche.prenom} ${fiche.nom}` : 'Employé'" taille="lg" @fermer="$emit('fermer')">
    <div v-if="erreur" class="alert alert-danger py-2" role="alert">{{ erreur }}</div>
    <div v-if="message" class="alert alert-success py-2" role="status">
      {{ message }}
      <div v-if="motDePasseAffiche" class="mt-1">Mot de passe provisoire à transmettre : <code class="fs-6">{{ motDePasseAffiche }}</code></div>
    </div>

    <template v-if="fiche">
      <form id="form-fiche" class="row g-3" @submit.prevent="enregistrer">
        <div class="col-sm-6">
          <label for="f-nom" class="form-label">Nom</label>
          <input id="f-nom" v-model.trim="identite.nom" class="form-control" required maxlength="100" />
        </div>
        <div class="col-sm-6">
          <label for="f-prenom" class="form-label">Prénom</label>
          <input id="f-prenom" v-model.trim="identite.prenom" class="form-control" required maxlength="100" />
        </div>
        <div class="col-sm-6">
          <label for="f-identifiant" class="form-label">Identifiant de connexion</label>
          <input id="f-identifiant" v-model.trim="identite.identifiant" class="form-control" required pattern="[a-z0-9][a-z0-9._\-]{2,39}" />
        </div>
        <div class="col-12">
          <div class="form-label mb-1">Contrat</div>
          <table class="table table-sm mb-1">
            <thead>
              <tr><th>Heures / mois</th><th>Début</th><th>Fin</th><th></th></tr>
            </thead>
            <tbody>
              <tr v-for="c in contratsEdites" :key="c.id">
                <td><input v-model="c.heures_mensuelles" type="number" min="1" step="0.01" class="form-control form-control-sm" aria-label="Heures par mois" /></td>
                <td><input v-model="c.date_debut" type="date" class="form-control form-control-sm" aria-label="Début" /></td>
                <td><input v-model="c.date_fin" type="date" class="form-control form-control-sm" aria-label="Fin" /></td>
                <td class="text-end">
                  <button v-if="contratsEdites.length > 1" type="button" class="btn btn-sm btn-outline-danger" title="Supprimer ce contrat" @click="supprimerContrat(c)">
                    <i class="bi bi-trash"></i>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
          <div class="form-text">Pour un changement de contrat, utilisez « Avenant » ci-dessous.</div>
        </div>
        <div class="col-12 d-flex justify-content-end">
          <button type="submit" class="btn btn-primary">Enregistrer</button>
        </div>
      </form>

      <div class="d-flex flex-wrap gap-2 mt-3">
        <template v-if="enPoste">
          <button type="button" class="btn btn-outline-primary" :class="{ active: panneau === 'avenant' }" @click="basculer('avenant')">
            <i class="bi bi-pencil-square"></i> Avenant
          </button>
          <button type="button" class="btn btn-outline-danger" :class="{ active: panneau === 'depart' }" @click="basculer('depart')">
            <i class="bi bi-box-arrow-right"></i> Départ
          </button>
          <button type="button" class="btn btn-outline-secondary" :class="{ active: panneau === 'mdp' }" @click="basculer('mdp')">
            <i class="bi bi-key"></i> Mot de passe oublié
          </button>
        </template>
        <button v-else type="button" class="btn btn-outline-primary" :class="{ active: panneau === 'retour' }" @click="basculer('retour')">
          <i class="bi bi-arrow-return-left"></i> Retour de l'employé
        </button>
      </div>

      <form v-if="panneau === 'avenant'" class="border rounded p-3 mt-3" @submit.prevent="avenant">
        <h6>Avenant</h6>
        <div class="row g-3 align-items-end">
          <div class="col-sm-6">
            <label for="a-heures" class="form-label">Nouvelles heures / mois</label>
            <input id="a-heures" v-model="formAvenant.heures_mensuelles" type="number" min="1" step="0.01" class="form-control" required />
          </div>
          <div class="col-sm-6">
            <label for="a-debut" class="form-label">À partir du</label>
            <input id="a-debut" v-model="formAvenant.date_debut" type="date" class="form-control" required />
          </div>
          <div class="col-12 d-flex justify-content-end">
            <button type="submit" class="btn btn-primary">Appliquer l'avenant</button>
          </div>
        </div>
      </form>

      <form v-if="panneau === 'depart'" class="border rounded p-3 mt-3" @submit.prevent="depart">
        <h6>Départ</h6>
        <div class="row g-3 align-items-end">
          <div class="col-sm-6">
            <label for="d-sortie" class="form-label">Dernier jour sous contrat</label>
            <input id="d-sortie" v-model="formDepart.date_sortie" type="date" class="form-control" required />
          </div>
          <div class="col-sm-6">
            <div class="form-text">Le compte est désactivé immédiatement. Ses données sont conservées.</div>
          </div>
          <div class="col-12 d-flex justify-content-end">
            <button type="submit" class="btn btn-danger">Enregistrer le départ</button>
          </div>
        </div>
      </form>

      <div v-if="panneau === 'mdp'" class="border rounded p-3 mt-3">
        <h6>Mot de passe oublié</h6>
        <div class="row g-3 align-items-center">
          <div class="col-sm-9">
            <div class="form-text">Génère un nouveau mot de passe provisoire, à changer à la prochaine connexion.</div>
          </div>
          <div class="col-sm-3 d-flex justify-content-end">
            <button type="button" class="btn btn-secondary" :disabled="!fiche.actif" @click="reinitialiser">Générer</button>
          </div>
        </div>
      </div>

      <form v-if="panneau === 'retour'" class="border rounded p-3 mt-3" @submit.prevent="retour">
        <h6>Retour de l'employé</h6>
        <div class="row g-3 align-items-end">
          <div class="col-sm-6">
            <label for="r-entree" class="form-label">Date de retour</label>
            <input id="r-entree" v-model="formRetour.date_entree" type="date" class="form-control" required />
          </div>
          <div class="col-sm-6">
            <label for="r-heures" class="form-label">Contrat (heures / mois)</label>
            <input id="r-heures" v-model="formRetour.heures_mensuelles" type="number" min="1" step="0.01" class="form-control" required />
          </div>
          <div class="col-12 d-flex justify-content-end">
            <button type="submit" class="btn btn-primary">Réactiver le compte</button>
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

const props = defineProps({ employeId: { type: Number, default: null } })
const emit = defineEmits(['fermer', 'modifie'])

const fiche = ref(null)
const erreur = ref('')
const message = ref('')
const motDePasseAffiche = ref('')
const panneau = ref(null)
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
  panneau.value = null
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
    return true
  } catch (error) {
    erreur.value = await messageErreur(error)
    return false
  }
}

const basculer = (nom) => {
  panneau.value = panneau.value === nom ? null : nom
}

const url = () => `/employes/${props.employeId}`

const contratModifie = (c) => {
  const origine = fiche.value.contrats.find((o) => o.id === c.id)
  return Number(origine.heures_mensuelles) !== Number(c.heures_mensuelles)
    || origine.date_debut !== c.date_debut
    || (origine.date_fin || '') !== (c.date_fin || '')
}

const enregistrer = () => executer(async () => {
  let reponse = await api.put(url(), identite)
  for (const c of contratsEdites.value.filter(contratModifie)) {
    reponse = await api.put(`${url()}/contrats/${c.id}`, {
      heures_mensuelles: c.heures_mensuelles,
      date_debut: c.date_debut,
      date_fin: c.date_fin || null,
    })
  }
  return reponse
}, 'Fiche enregistrée.')

const supprimerContrat = (c) => {
  if (confirm('Supprimer ce contrat ?')) executer(() => api.delete(`${url()}/contrats/${c.id}`), 'Contrat supprimé.')
}

const avenant = async () => {
  if (await executer(() => api.post(`${url()}/contrats`, formAvenant), 'Avenant enregistré.')) panneau.value = null
}

const depart = async () => {
  if (!confirm(`Enregistrer le départ de ${fiche.value.prenom} ${fiche.value.nom} ? Son compte sera désactivé immédiatement.`)) return
  if (await executer(() => api.post(`${url()}/depart`, formDepart), 'Départ enregistré, compte désactivé.')) panneau.value = null
}

const retour = async () => {
  const motDePasse = genererMotDePasse()
  if (await executer(
    () => api.post(`${url()}/retour`, { ...formRetour, mot_de_passe_provisoire: motDePasse }),
    'Retour enregistré, compte réactivé.',
    motDePasse
  )) panneau.value = null
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
