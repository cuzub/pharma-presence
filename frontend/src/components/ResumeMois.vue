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

      <dt>Heures en plus</dt>
      <dd>{{ employe.total_heures ? `${formatNombre(employe.total_heures)} h` : 'Aucune' }}</dd>

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

      <dt>Déplacements validés</dt>
      <dd>
        {{ employe.total_km_valides ? `${formatNombre(employe.total_km_valides)} km` : 'Aucun' }}
        <div v-if="employe.deplacements_en_attente" class="small text-warning-emphasis">
          {{ employe.deplacements_en_attente }} en attente de validation
        </div>
      </dd>
    </dl>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { formatFr, formatNombre, joursDuMois } from '../utils/dates'

const props = defineProps({
  employe: { type: Object, required: true },
  mois: { type: String, default: '' }
})

const jours = computed(() => (props.mois ? joursDuMois(props.mois) : []))
const debutMois = computed(() => jours.value[0] || '0000-00-00')
const finMois = computed(() => jours.value[jours.value.length - 1] || '9999-12-31')
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
