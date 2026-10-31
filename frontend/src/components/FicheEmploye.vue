<template>
  <Modal :ouvert="!!employeId" :titre="fiche ? `${fiche.prenom} ${fiche.nom}` : 'Employé'" taille="lg" @fermer="$emit('fermer')">
    <div v-if="erreur" class="alert alert-danger py-2" role="alert">{{ erreur }}</div>
    <div v-if="message" class="alert alert-success py-2" role="status">{{ message }}</div>


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
          <div class="form-label mb-1">Contrats</div>
          <div v-for="c in contratsEdites" :key="c.id" class="row g-3 align-items-end mb-1">
            <div class="col-sm-4">
              <label :for="`c-heures-${c.id}`" class="form-label">Heures / mois</label>
              <input :id="`c-heures-${c.id}`" v-model="c.heures_mensuelles" type="number" min="1" step="0.01" class="form-control" required />
            </div>
            <div class="col-sm-3">
              <label :for="`c-debut-${c.id}`" class="form-label">Début</label>
              <input :id="`c-debut-${c.id}`" v-model="c.date_debut" type="date" class="form-control" required />
            </div>
            <div class="col-sm-3">
              <label :for="`c-fin-${c.id}`" class="form-label">Fin</label>
              <input :id="`c-fin-${c.id}`" v-model="c.date_fin" type="date" class="form-control" />
            </div>
            <div class="col-sm-2 text-sm-end">
              <button v-if="contratsEdites.length > 1" type="button" class="btn btn-outline-danger" title="Supprimer ce contrat" @click="supprimerContrat(c)">
                <i class="bi bi-trash"></i>
              </button>
            </div>
          </div>
          <div class="form-text">Pour un changement de contrat, utilisez le bouton « Avenant » dans la liste des employés.</div>
        </div>
      </form>

    </template>
    <template v-if="fiche" #footer>
      <button type="button" class="btn btn-outline-secondary" @click="$emit('fermer')">Annuler</button>
      <button type="submit" form="form-fiche" class="btn btn-primary">Enregistrer</button>
    </template>
  </Modal>
</template>

<script setup>
import { reactive, ref, watch } from 'vue'
import api, { messageErreur } from '../services/api'
import Modal from './Modal.vue'

const props = defineProps({ employeId: { type: Number, default: null } })
const emit = defineEmits(['fermer', 'modifie'])

const fiche = ref(null)
const erreur = ref('')
const message = ref('')
const identite = reactive({ nom: '', prenom: '', identifiant: '' })
const contratsEdites = ref([])

const appliquer = (donnees) => {
  fiche.value = donnees
  Object.assign(identite, { nom: donnees.nom, prenom: donnees.prenom, identifiant: donnees.identifiant })
  contratsEdites.value = donnees.contrats.map((c) => ({ ...c, date_fin: c.date_fin || '' }))
}

watch(() => props.employeId, async (id) => {
  fiche.value = null
  erreur.value = message.value = ''
  if (!id) return
  try {
    appliquer((await api.get(`/employes/${id}`)).data)
  } catch (error) {
    erreur.value = await messageErreur(error)
  }
})

const executer = async (requete, succes) => {
  erreur.value = message.value = ''
  try {
    const reponse = await requete()
    if (reponse.data?.contrats) appliquer(reponse.data)
    message.value = succes
    emit('modifie')
    return true
  } catch (error) {
    erreur.value = await messageErreur(error)
    return false
  }
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
</script>

