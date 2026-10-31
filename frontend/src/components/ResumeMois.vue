<template>
  <div class="carte">
    <h2 class="h6 text-uppercase text-muted">Résumé du mois</h2>
    <dl class="mb-0 resume">
      <dt>Contrat</dt>
      <dd>
        <template v-if="employe.contrats.length">
          <div v-for="c in employe.contrats" :key="c.id">
            {{ formatNombre(c.heures_mensuelles) }} h/mois
            <span v-if="c.date_debut > debutMois" class="text-muted small">à partir du {{ formatFr(c.date_debut) }}</span>
            <span v-if="c.date_fin && c.date_fin < finMois" class="text-muted small">jusqu'au {{ formatFr(c.date_fin) }}</span>
          </div>
        </template>
        <span v-else class="text-muted">Aucun contrat ce mois-ci</span>
      </dd>

      <dt>Heures en plus / en moins du mois</dt>
      <dd>
        <span
          v-if="Object.keys(employe.heures || {}).length || employe.regularisations?.length"
          :class="employe.total_minutes < 0 ? 'minutes-moins' : 'minutes-plus'"
        >
          {{ employe.total_minutes ? formatMinutes(employe.total_minutes) : '0' }}
        </span>
        <span v-else>Aucune</span>
        <div v-if="employe.regularisations?.length" class="small regularisation">
          dont régularisations : {{ formatMinutes(totalRegularisations) || '0' }}
        </div>
      </dd>

      <dt>Solde cumulé à fin de mois</dt>
      <dd data-solde>
        <span :class="['fw-semibold', employe.solde_minutes < 0 ? 'minutes-moins' : 'minutes-plus']">
          {{ employe.solde_minutes ? formatMinutes(employe.solde_minutes) : '0' }}
        </span>
      </dd>

      <dt>Absences</dt>
      <dd>
        <div v-for="a in employe.absences" :key="a.id" class="mb-1">
          <span class="pastille-motif" :style="{ background: a.motif_couleur }">{{ a.motif_libelle }}</span>
          <div class="small">
            du {{ formatFr(a.date_debut) }} — {{ a.date_reprise ? `reprise le ${formatFr(a.date_reprise)}` : 'en cours' }}
          </div>
        </div>
        <span v-if="!employe.absences.length" class="text-muted">Aucune</span>
      </dd>

      <dt>Déplacements</dt>
      <dd>{{ employe.total_km ? `${formatNombre(employe.total_km)} km` : 'Aucun' }}</dd>
    </dl>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { formatFr, formatMinutes, formatNombre, joursDuMois } from '../utils/dates'

const props = defineProps({
  employe: { type: Object, required: true },
  mois: { type: String, default: '' }
})

const jours = computed(() => (props.mois ? joursDuMois(props.mois) : []))
const debutMois = computed(() => jours.value[0] || '0000-00-00')
const finMois = computed(() => jours.value[jours.value.length - 1] || '9999-12-31')
const totalRegularisations = computed(() => (props.employe.regularisations || []).reduce((s, r) => s + r.minutes, 0))
</script>

<style scoped>
.resume dt {
  font-size: 0.8rem;
  color: #6c757d;
  font-weight: 600;
  margin-top: 0.75rem;
}

.resume dd {
  margin-bottom: 0;
}
</style>
