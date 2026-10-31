<template>
  <Modal :ouvert="!!action" :titre="titre" @fermer="fermer">
    <div v-if="erreur" class="alert alert-danger py-2" role="alert">{{ erreur }}</div>
    <div v-if="motDePasseAffiche" class="alert alert-success py-2" role="status">
      Nouveau mot de passe provisoire : <code class="fs-6">{{ motDePasseAffiche }}</code>
      <div class="small mt-1">À transmettre à l'employé ; il devra le changer à sa prochaine connexion.</div>
    </div>

    <form v-if="action && !motDePasseAffiche" id="form-action" class="row g-3" @submit.prevent="valider">
      <template v-if="action.type === 'avenant'">
        <div class="col-sm-6">
          <label for="a-heures" class="form-label">Nouvelles heures / mois</label>
          <input id="a-heures" v-model="formulaire.heures_mensuelles" type="number" min="1" step="0.01" class="form-control" required />
        </div>
        <div class="col-sm-6">
          <label for="a-debut" class="form-label">À partir du</label>
          <input id="a-debut" v-model="formulaire.date_debut" type="date" class="form-control" required />
        </div>
        <div class="col-12">
          <div class="form-text">Le nouveau contrat remplace le précédent à partir de cette date.</div>
        </div>
      </template>

      <template v-else-if="action.type === 'depart'">
        <div class="col-12">
          <label for="d-sortie" class="form-label">Dernier jour sous contrat</label>
          <input id="d-sortie" v-model="formulaire.date_sortie" type="date" class="form-control" required />
          <div class="form-text">Le compte est désactivé immédiatement. Ses données sont conservées.</div>
        </div>
      </template>

      <template v-else-if="action.type === 'mdp'">
        <div class="col-12">
          <div class="form-text">Génère un nouveau mot de passe provisoire, à changer à la prochaine connexion.</div>
        </div>
      </template>

      <template v-else-if="action.type === 'retour'">
        <div class="col-sm-6">
          <label for="r-entree" class="form-label">Date de retour</label>
          <input id="r-entree" v-model="formulaire.date_entree" type="date" class="form-control" required />
        </div>
        <div class="col-sm-6">
          <label for="r-heures" class="form-label">Contrat (heures / mois)</label>
          <input id="r-heures" v-model="formulaire.heures_mensuelles" type="number" min="1" step="0.01" class="form-control" required />
        </div>
      </template>
    </form>

    <template #footer>
      <button type="button" class="btn btn-outline-secondary" @click="fermer">{{ motDePasseAffiche ? 'Fermer' : 'Annuler' }}</button>
      <button v-if="!motDePasseAffiche" type="submit" form="form-action" :class="['btn', action?.type === 'depart' ? 'btn-danger' : 'btn-primary']">
        {{ libelleBouton }}
      </button>
    </template>
  </Modal>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import api, { messageErreur } from '../services/api'
import { aujourdhuiIso } from '../utils/dates'
import { genererMotDePasse } from '../utils/motDePasse'
import Modal from './Modal.vue'

const props = defineProps({
  action: { type: Object, default: null }
})
const emit = defineEmits(['fermer', 'modifie'])

const erreur = ref('')
const motDePasseAffiche = ref('')
const formulaire = reactive({ heures_mensuelles: '', date_debut: '', date_sortie: '', date_entree: '' })

const LIBELLES = {
  avenant: 'Avenant',
  depart: 'Départ',
  mdp: 'Mot de passe oublié',
  retour: "Retour de l'employé"
}
const LIBELLES_BOUTON = {
  avenant: "Appliquer l'avenant",
  depart: 'Enregistrer le départ',
  mdp: 'Générer un mot de passe',
  retour: 'Réactiver le compte'
}

const titre = computed(() => props.action
  ? `${LIBELLES[props.action.type]} · ${props.action.employe.prenom} ${props.action.employe.nom}`
  : '')
const libelleBouton = computed(() => LIBELLES_BOUTON[props.action?.type] || '')

watch(() => props.action, (action) => {
  erreur.value = ''
  motDePasseAffiche.value = ''
  if (!action) return
  const e = action.employe
  Object.assign(formulaire, {
    heures_mensuelles: e.heures_mensuelles ?? '',
    date_debut: '',
    date_sortie: aujourdhuiIso(),
    date_entree: aujourdhuiIso()
  })
}, { immediate: true })

const fermer = () => emit('fermer')

const envoyer = async (requete, succes, motDePasse = '') => {
  erreur.value = ''
  try {
    await requete()
    motDePasseAffiche.value = motDePasse
    emit('modifie', succes)
    if (!motDePasse) fermer()
  } catch (error) {
    erreur.value = await messageErreur(error)
  }
}

const valider = () => {
  const id = props.action.employe.id
  const { type, employe } = props.action
  if (type === 'avenant') {
    return envoyer(() => api.post(`/employes/${id}/contrats`, { ...formulaire }), 'Avenant enregistré.')
  }
  if (type === 'depart') {
    if (!confirm(`Enregistrer le départ de ${employe.prenom} ${employe.nom} ? Son compte sera désactivé immédiatement.`)) return
    return envoyer(() => api.post(`/employes/${id}/depart`, { date_sortie: formulaire.date_sortie }), 'Départ enregistré, compte désactivé.')
  }
  if (type === 'mdp') {
    const motDePasse = genererMotDePasse()
    return envoyer(
      () => api.post(`/employes/${id}/mot-de-passe`, { mot_de_passe_provisoire: motDePasse }),
      'Nouveau mot de passe provisoire défini.',
      motDePasse
    )
  }
  const motDePasse = genererMotDePasse()
  return envoyer(
    () => api.post(`/employes/${id}/retour`, { date_entree: formulaire.date_entree, heures_mensuelles: formulaire.heures_mensuelles, mot_de_passe_provisoire: motDePasse }),
    'Retour enregistré, compte réactivé.',
    motDePasse
  )
}
</script>
