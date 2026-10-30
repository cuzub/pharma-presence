<template>
  <div class="d-flex align-items-center gap-2 mois-navigateur">
    <button type="button" class="btn btn-outline-secondary btn-sm" title="Mois précédent" aria-label="Mois précédent" @click="changer(-1)">
      <i class="bi bi-chevron-left"></i>
    </button>
    <h2 class="h5 mb-0 text-capitalize mois-titre">{{ libelleMois(modelValue) }}</h2>
    <button type="button" class="btn btn-outline-secondary btn-sm" title="Mois suivant" aria-label="Mois suivant" @click="changer(1)">
      <i class="bi bi-chevron-right"></i>
    </button>
    <button v-if="modelValue !== moisCourant()" type="button" class="btn btn-link btn-sm" @click="$emit('update:modelValue', moisCourant())">
      Ce mois-ci
    </button>
  </div>
</template>

<script setup>
import { decalerMois, libelleMois, moisCourant } from '../utils/dates'

const props = defineProps({ modelValue: { type: String, required: true } })
const emit = defineEmits(['update:modelValue'])

const changer = (delta) => emit('update:modelValue', decalerMois(props.modelValue, delta))
</script>
