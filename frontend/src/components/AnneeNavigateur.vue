<template>
  <div class="d-flex align-items-center gap-2 annee-navigateur">
    <button
      type="button"
      :class="['btn btn-outline-secondary btn-sm', { invisible: estCourante }]"
      :title="`Revenir à l'année en cours (${anneeCourante()})`"
      aria-label="Revenir à l'année en cours"
      :aria-hidden="estCourante ? 'true' : undefined"
      :tabindex="estCourante ? -1 : undefined"
      @click="$emit('update:modelValue', anneeCourante())"
    >
      <i class="bi bi-calendar-check"></i>
    </button>
    <button type="button" class="btn btn-outline-secondary btn-sm" title="Année précédente" aria-label="Année précédente" @click="changer(-1)">
      <i class="bi bi-chevron-left"></i>
    </button>
    <h2 class="h5 mb-0 navigateur-titre annee-titre">{{ modelValue }}</h2>
    <button type="button" class="btn btn-outline-secondary btn-sm" title="Année suivante" aria-label="Année suivante" @click="changer(1)">
      <i class="bi bi-chevron-right"></i>
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { anneeCourante } from '../utils/dates'

const props = defineProps({ modelValue: { type: Number, required: true } })
const emit = defineEmits(['update:modelValue'])

// Le bouton reste en place (invisible) pour que les flèches ne bougent jamais.
const estCourante = computed(() => props.modelValue === anneeCourante())

const changer = (delta) => emit('update:modelValue', props.modelValue + delta)
</script>
