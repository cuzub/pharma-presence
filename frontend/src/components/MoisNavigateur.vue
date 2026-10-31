<template>
  <div class="d-flex align-items-center gap-2 mois-navigateur">
    <button
      type="button"
      :class="['btn btn-outline-secondary btn-sm', { invisible: estCourant }]"
      :title="`Revenir au mois en cours (${libelleMois(moisCourant())})`"
      aria-label="Revenir au mois en cours"
      :aria-hidden="estCourant ? 'true' : undefined"
      :tabindex="estCourant ? -1 : undefined"
      @click="$emit('update:modelValue', moisCourant())"
    >
      <i class="bi bi-calendar-check"></i>
    </button>
    <button type="button" class="btn btn-outline-secondary btn-sm" title="Mois précédent" aria-label="Mois précédent" @click="changer(-1)">
      <i class="bi bi-chevron-left"></i>
    </button>
    <h2 class="h5 mb-0 text-capitalize navigateur-titre mois-titre">{{ libelleMois(modelValue) }}</h2>
    <button type="button" class="btn btn-outline-secondary btn-sm" title="Mois suivant" aria-label="Mois suivant" @click="changer(1)">
      <i class="bi bi-chevron-right"></i>
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { decalerMois, libelleMois, moisCourant } from '../utils/dates'

const props = defineProps({ modelValue: { type: String, required: true } })
const emit = defineEmits(['update:modelValue'])

// Le bouton reste en place (invisible) pour que les flèches ne bougent jamais.
const estCourant = computed(() => props.modelValue === moisCourant())

const changer = (delta) => emit('update:modelValue', decalerMois(props.modelValue, delta))
</script>
