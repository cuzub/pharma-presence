<template>
  <div :class="['calendrier', { 'lecture-seule': lectureSeule }]">
    <div class="calendrier-entete">
      <div v-for="jour in JOURS_COURTS" :key="jour" class="calendrier-jour-semaine">{{ jour }}</div>
    </div>
    <div class="calendrier-grille">
      <div v-for="n in decalage" :key="`vide-${n}`" class="calendrier-case vide"></div>
      <div
        v-for="jour in jours"
        :key="jour.iso"
        :class="['calendrier-case', jour.classes, { cliquable: !lectureSeule }]"
        :title="jour.titre"
        :data-jour="jour.iso"
        :role="lectureSeule ? undefined : 'button'"
        :tabindex="lectureSeule ? undefined : 0"
        @click="choisir(jour.iso)"
        @keydown.enter.self.prevent="choisir(jour.iso)"
        @keydown.space.self.prevent="choisir(jour.iso)"
      >
        <div class="d-flex justify-content-between align-items-start">
          <span class="numero">{{ jour.numero }}</span>
          <span v-if="jour.heures" class="badge text-bg-success heures">+{{ formatNombre(jour.heures) }} h</span>
        </div>
        <div v-if="jour.ferie" class="libelle-special">{{ jour.ferie }}</div>
        <div v-else-if="jour.fermeture" class="libelle-special"><i class="bi bi-shop"></i> {{ jour.fermeture }}</div>
        <div
          v-for="d in jour.deplacements"
          :key="d.id"
          :class="['ligne-deplacement', `statut-${d.statut}`]"
          :title="titreDeplacement(d)"
          data-deplacement
        >
          <i class="bi bi-car-front"></i>
          <span class="text-truncate flex-grow-1">{{ d.motif }}</span>
          <span class="text-nowrap">{{ formatNombre(d.km) }} km</span>
          <button
            v-if="deplacementModifiable(d)"
            type="button"
            class="crayon"
            :aria-label="`Modifier le déplacement ${d.motif}`"
            title="Modifier"
            @click.stop="$emit('modifier-deplacement', d)"
          >
            <i class="bi bi-pencil"></i>
          </button>
        </div>
        <span v-if="jour.absence" class="pastille-motif mt-auto" :style="{ background: jour.absence.motif_couleur }">
          {{ jour.absence.motif_libelle }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { STATUTS_DEPLACEMENT } from '../utils/statuts'
import { JOURS_COURTS, absenceDuJour, aujourdhuiIso, ferie, formatFr, formatNombre, jourSemaine, joursDuMois } from '../utils/dates'

const props = defineProps({
  mois: { type: String, required: true },
  absences: { type: Array, default: () => [] },
  heures: { type: Object, default: () => ({}) },
  deplacements: { type: Array, default: () => [] },
  // Affiche le crayon de modification sur un déplacement.
  deplacementModifiable: { type: Function, default: () => true },
  joursFermeture: { type: Array, default: () => [] },
  // Si fournis, les jours hors contrat sont hachurés.
  contrats: { type: Array, default: null },
  lectureSeule: { type: Boolean, default: false }
})
const emit = defineEmits(['choisir-jour', 'modifier-deplacement'])

const choisir = (iso) => {
  if (!props.lectureSeule) emit('choisir-jour', iso)
}

const titreDeplacement = (d) =>
  [`${d.motif} — ${formatNombre(d.km)} km`, STATUTS_DEPLACEMENT[d.statut]?.libelle, d.motif_refus].filter(Boolean).join(' — ')

const decalage = computed(() => jourSemaine(`${props.mois}-01`))

const horsContrat = (iso) =>
  props.contrats !== null && !props.contrats.some((c) => c.date_debut <= iso && (!c.date_fin || c.date_fin >= iso))

const jours = computed(() => {
  const aujourdhui = aujourdhuiIso()
  const fermetures = new Map(props.joursFermeture.map((j) => [j.date, j.libelle || 'Fermeture']))
  const deplacementsParJour = new Map()
  for (const d of props.deplacements) deplacementsParJour.set(d.date, [...(deplacementsParJour.get(d.date) || []), d])
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
      deplacements: deplacementsParJour.get(iso) || [],
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

.calendrier-case.cliquable {
  cursor: pointer;
}

.calendrier-case.cliquable:hover,
.calendrier-case.cliquable:focus-visible {
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

.ligne-deplacement {
  display: flex;
  align-items: center;
  gap: 3px;
  padding: 1px 4px;
  border-radius: 4px;
  border-left: 3px solid;
  font-size: 0.72rem;
  background: #f1f8e9;
  border-color: var(--pharma-vert);
}

.ligne-deplacement.statut-en_attente {
  background: #fff8e1;
  border-color: #ffc107;
}

.ligne-deplacement.statut-refuse {
  background: #fdecea;
  border-color: #dc3545;
}

.crayon {
  border: none;
  background: transparent;
  padding: 0 2px;
  line-height: 1;
  color: #495057;
}

.crayon:hover {
  color: var(--pharma-vert);
}

.libelle-special {
  font-size: 0.7rem;
  color: #795548;
}
</style>
