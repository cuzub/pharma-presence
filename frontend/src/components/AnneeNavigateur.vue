<template>
  <div class="d-flex align-items-center gap-2 annee-navigateur">
    <button type="button" class="btn btn-outline-secondary btn-sm" title="Année précédente" aria-label="Année précédente" @click="changer(-1)">
      <i class="bi bi-chevron-left"></i>
    </button>
    <h2 class="h5 mb-0 annee-titre">{{ modelValue }}</h2>
    <button type="button" class="btn btn-outline-secondary btn-sm" title="Année suivante" aria-label="Année suivante" @click="changer(1)">
      <i class="bi bi-chevron-right"></i>
    </button>
    <button v-if="modelValue !== anneeCourante()" type="button" class="btn btn-link btn-sm" @click="$emit('update:modelValue', anneeCourante())">
      Cette année
    </button>
  </div>
</template>

<script setup>
import { anneeCourante } from '../utils/dates'

const props = defineProps({ modelValue: { type: Number, required: true } })
const emit = defineEmits(['update:modelValue'])

const changer = (delta) => emit('update:modelValue', props.modelValue + delta)
</script>
