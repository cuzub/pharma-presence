<template>
  <div>
    <h1 class="h4 mb-3">Paramètres</h1>
    <div v-if="erreur" class="alert alert-danger">{{ erreur }}</div>

    <div class="row g-3">
      <div class="col-lg-7">
        <div class="carte">
          <h2 class="h6">Motifs d'absence</h2>
          <p class="form-text">Un motif désactivé n'est plus proposé, mais reste visible sur les absences déjà saisies.</p>
          <table class="table table-sm">
            <thead>
              <tr><th>Code</th><th>Libellé</th><th>Couleur</th><th>Bloque heures et déplacements</th><th>Actif</th><th></th></tr>
            </thead>
            <tbody>
              <tr v-for="m in motifs" :key="m.id">
                <td><span class="pastille-motif" :style="{ background: m.couleur }">{{ m.code }}</span></td>
                <td><input v-model.trim="m.libelle" class="form-control form-control-sm" aria-label="Libellé" /></td>
                <td><input v-model="m.couleur" type="color" class="form-control form-control-sm form-control-color" aria-label="Couleur" /></td>
                <td class="text-center"><input v-model="m.bloque_saisie" type="checkbox" class="form-check-input" aria-label="Bloque heures et déplacements" /></td>
                <td><input v-model="m.actif" type="checkbox" class="form-check-input" aria-label="Actif" /></td>
                <td class="text-end">
                  <button type="button" class="btn btn-sm btn-outline-primary" @click="enregistrerMotif(m)">Enregistrer</button>
                </td>
              </tr>
            </tbody>
          </table>
          <form class="row g-2 align-items-end" @submit.prevent="ajouterMotif">
            <div class="col-2">
              <label for="m-code" class="form-label small mb-1">Code</label>
              <input id="m-code" v-model.trim="nouveauMotif.code" class="form-control form-control-sm" maxlength="20" required />
            </div>
            <div class="col-4">
              <label for="m-libelle" class="form-label small mb-1">Libellé</label>
              <input id="m-libelle" v-model.trim="nouveauMotif.libelle" class="form-control form-control-sm" maxlength="80" required />
            </div>
            <div class="col-2">
              <label for="m-couleur" class="form-label small mb-1">Couleur</label>
              <input id="m-couleur" v-model="nouveauMotif.couleur" type="color" class="form-control form-control-sm form-control-color" />
            </div>
            <div class="col-2 pb-1">
              <div class="form-check">
                <input id="m-bloque" v-model="nouveauMotif.bloque_saisie" type="checkbox" class="form-check-input" />
                <label for="m-bloque" class="form-check-label small">Bloque heures et déplacements</label>
              </div>
            </div>
            <div class="col-2">
              <button type="submit" class="btn btn-sm btn-primary w-100">Ajouter</button>
            </div>
          </form>
        </div>
      </div>

      <div class="col-lg-5">
        <div class="carte">
          <h2 class="h6">Jours de fermeture de la pharmacie</h2>
          <p class="form-text">Jours fériés et dimanches sont déjà grisés automatiquement. Ajoutez ici les autres fermetures (ponts, inventaire…).</p>
          <form class="row g-2 align-items-end mb-3" @submit.prevent="ajouterFermeture">
            <div class="col-5">
              <label for="f-date" class="form-label small mb-1">Date</label>
              <input id="f-date" v-model="nouvelleFermeture.date" type="date" class="form-control form-control-sm" required />
            </div>
            <div class="col-5">
              <label for="f-libelle" class="form-label small mb-1">Libellé</label>
              <input id="f-libelle" v-model.trim="nouvelleFermeture.libelle" class="form-control form-control-sm" maxlength="120" placeholder="ex : Pont" />
            </div>
            <div class="col-2">
              <button type="submit" class="btn btn-sm btn-primary w-100">Ajouter</button>
            </div>
          </form>
          <ul class="list-group list-group-flush">
            <li v-for="f in fermeturesAVenir" :key="f.id" class="list-group-item d-flex justify-content-between align-items-center px-0">
              <span>{{ formatFr(f.date) }} <span class="text-muted small">{{ f.libelle }}</span></span>
              <button type="button" class="btn btn-sm btn-outline-danger" title="Supprimer" @click="supprimerFermeture(f)">
                <i class="bi bi-trash"></i>
              </button>
            </li>
            <li v-if="!fermeturesAVenir.length" class="list-group-item text-muted small px-0">Aucune fermeture à venir.</li>
          </ul>
        </div>
      </div>

      <div class="col-lg-7">
        <div class="carte">
          <h2 class="h6">Motifs de déplacement</h2>
          <p class="form-text">
            Destinations habituelles avec leur distance : lors de la saisie d'un déplacement, les km sont remplis automatiquement.
            « Autre » est toujours proposé pour saisir une distance libre. Changer une distance ne modifie pas les déplacements déjà saisis.
          </p>
          <table class="table table-sm">
            <thead>
              <tr><th>Motif</th><th class="col-km">Km</th><th>Actif</th><th></th></tr>
            </thead>
            <tbody>
              <tr v-for="m in motifsDeplacement" :key="m.id">
                <td><input v-model.trim="m.libelle" class="form-control form-control-sm" maxlength="80" aria-label="Motif" /></td>
                <td><input v-model.number="m.km" type="number" min="0.1" max="5000" step="0.1" class="form-control form-control-sm" aria-label="Km" /></td>
                <td><input v-model="m.actif" type="checkbox" class="form-check-input" aria-label="Actif" /></td>
                <td class="text-end">
                  <button type="button" class="btn btn-sm btn-outline-primary" @click="enregistrerMotifDeplacement(m)">Enregistrer</button>
                </td>
              </tr>
              <tr v-if="!motifsDeplacement.length">
                <td colspan="4" class="text-muted small">Aucun motif pour l'instant (ex : Domitis 2 km, Orgères 5 km, LCL 30 km).</td>
              </tr>
            </tbody>
          </table>
          <form class="row g-2 align-items-end" @submit.prevent="ajouterMotifDeplacement">
            <div class="col-6">
              <label for="md-libelle" class="form-label small mb-1">Motif</label>
              <input id="md-libelle" v-model.trim="nouveauMotifDeplacement.libelle" class="form-control form-control-sm" maxlength="80" required placeholder="ex : Domitis" />
            </div>
            <div class="col-3">
              <label for="md-km" class="form-label small mb-1">Km</label>
              <input id="md-km" v-model.number="nouveauMotifDeplacement.km" type="number" min="0.1" max="5000" step="0.1" class="form-control form-control-sm" required />
            </div>
            <div class="col-3">
              <button type="submit" class="btn btn-sm btn-primary w-100">Ajouter</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import api, { messageErreur } from '../../services/api'
import { useReferentielStore } from '../../stores/referentiel'
import { ajouterJours, aujourdhuiIso, formatFr } from '../../utils/dates'

const referentiel = useReferentielStore()
const motifs = ref([])
const motifsDeplacement = ref([])
const fermetures = ref([])
const erreur = ref('')
const nouveauMotif = reactive({ code: '', libelle: '', couleur: '#6c757d', bloque_saisie: true })
const nouveauMotifDeplacement = reactive({ libelle: '', km: '' })
const nouvelleFermeture = reactive({ date: '', libelle: '' })

const fermeturesAVenir = computed(() => {
  const limite = ajouterJours(aujourdhuiIso(), -31)
  return fermetures.value.filter((f) => f.date >= limite)
})

const charger = async () => {
  try {
    motifs.value = (await referentiel.chargerMotifs(true)).map((m) => ({ ...m }))
    motifsDeplacement.value = (await referentiel.chargerMotifsDeplacement(true)).map((m) => ({ ...m }))
    fermetures.value = (await api.get('/jours-fermeture')).data
  } catch (error) {
    erreur.value = await messageErreur(error)
  }
}

const action = async (requete) => {
  erreur.value = ''
  try {
    await requete()
    await charger()
    return true
  } catch (error) {
    erreur.value = await messageErreur(error)
    return false
  }
}

const enregistrerMotif = (m) => action(() => api.put(`/motifs/${m.id}`, m))

const ajouterMotif = async () => {
  if (await action(() => api.post('/motifs', nouveauMotif))) Object.assign(nouveauMotif, { code: '', libelle: '', couleur: '#6c757d', bloque_saisie: true })
}

const enregistrerMotifDeplacement = (m) => action(() => api.put(`/deplacements/motifs/${m.id}`, m))

const ajouterMotifDeplacement = async () => {
  if (await action(() => api.post('/deplacements/motifs', nouveauMotifDeplacement))) {
    Object.assign(nouveauMotifDeplacement, { libelle: '', km: '' })
  }
}

const ajouterFermeture = async () => {
  if (await action(() => api.post('/jours-fermeture', nouvelleFermeture))) Object.assign(nouvelleFermeture, { date: '', libelle: '' })
}

const supprimerFermeture = (f) => action(() => api.delete(`/jours-fermeture/${f.id}`))

onMounted(charger)
</script>

<style scoped>
.col-km {
  width: 7rem;
}
</style>
