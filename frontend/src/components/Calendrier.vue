<template>
  <div :class="['calendrier', { 'lecture-seule': lectureSeule }]">
    <div class="calendrier-entete">
      <div v-for="jour in JOURS_COURTS" :key="jour" class="calendrier-jour-semaine">{{ jour }}</div>
    </div>
    <div class="calendrier-grille">
      <div v-for="n in decalage" :key="`vide-${n}`" class="calendrier-case vide"></div>
      <component
        :is="lectureSeule ? 'div' : 'button'"
        v-for="jour in jours"
        :key="jour.iso"
        :type="lectureSeule ? undefined : 'button'"
        :class="['calendrier-case', jour.classes]"
        :title="jour.titre"
        :data-jour="jour.iso"
        @click="!lectureSeule && $emit('choisir-jour', jour.iso)"
      >
        <div class="d-flex justify-content-between align-items-start">
          <span class="numero">{{ jour.numero }}</span>
          <span v-if="jour.heures" class="badge text-bg-success heures">+{{ formatNombre(jour.heures) }} h</span>
        </div>
        <div v-if="jour.ferie" class="libelle-special">{{ jour.ferie }}</div>
        <div v-else-if="jour.fermeture" class="libelle-special"><i class="bi bi-shop"></i> {{ jour.fermeture }}</div>
        <span v-if="jour.absence" class="pastille-motif mt-auto" :style="{ background: jour.absence.motif_couleur }">
          {{ jour.absence.motif_libelle }}
        </span>
      </component>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { JOURS_COURTS, absenceDuJour, aujourdhuiIso, ferie, formatFr, formatNombre, jourSemaine, joursDuMois } from '../utils/dates'

const props = defineProps({
  mois: { type: String, required: true },
  absences: { type: Array, default: () => [] },
  heures: { type: Object, default: () => ({}) },
  joursFermeture: { type: Array, default: () => [] },
  // Si fournis, les jours hors contrat sont hachurés.
  contrats: { type: Array, default: null },
  lectureSeule: { type: Boolean, default: false }
})
defineEmits(['choisir-jour'])

const decalage = computed(() => jourSemaine(`${props.mois}-01`))

const horsContrat = (iso) =>
  props.contrats !== null && !props.contrats.some((c) => c.date_debut <= iso && (!c.date_fin || c.date_fin >= iso))

const jours = computed(() => {
  const aujourdhui = aujourdhuiIso()
  const fermetures = new Map(props.joursFermeture.map((j) => [j.date, j.libelle || 'Fermeture']))
  return joursDuMois(props.mois).map((iso) => {
    const absence = absenceDuJour(props.absences, iso)
    const libelleFerie = ferie(iso)
    const fermeture = fermetures.get(iso) || null
    const heures = props.heures[iso] || 0
    const titre = [formatFr(iso), libelleFerie, fermeture, absence?.motif_libelle, heures ? `+${formatNombre(heures)} h` : null]
      .filter(Boolean)
      .join(' — ')
    return {
      iso,
      numero: Number(iso.slice(8)),
      absence,
      heures,
      ferie: libelleFerie,
      fermeture,
      titre,
      classes: {
        dimanche: jourSemaine(iso) === 6,
        ferie: !!libelleFerie,
        fermeture: !!fermeture,
        'hors-contrat': horsContrat(iso),
        aujourdhui: iso === aujourdhui
      }
    }
  })
})
</script>

<style scoped>
.calendrier-entete,
.calendrier-grille {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 4px;
}

.calendrier-jour-semaine {
  text-align: center;
  font-weight: 600;
  font-size: 0.8rem;
  color: #6c757d;
  padding-bottom: 4px;
}

.calendrier-case {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 2px;
  min-height: 84px;
  padding: 6px;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  background: #fff;
  text-align: left;
  font-size: 0.85rem;
}

button.calendrier-case:hover {
  border-color: var(--pharma-vert);
  box-shadow: 0 0 0 2px rgba(46, 125, 50, 0.15);
}

.calendrier-case.vide {
  border: none;
  background: transparent;
}

.calendrier-case.dimanche {
  background: var(--case-dimanche);
}

.calendrier-case.ferie {
  background: var(--case-ferie);
}

.calendrier-case.fermeture {
  background: var(--case-fermeture);
}

.calendrier-case.hors-contrat {
  background: var(--case-hors-contrat);
  color: #9e9e9e;
}

.calendrier-case.aujourdhui {
  border: 2px solid var(--pharma-vert);
}

.numero {
  font-weight: 600;
}

.heures {
  font-size: 0.7rem;
}

.libelle-special {
  font-size: 0.7rem;
  color: #795548;
}
</style>
