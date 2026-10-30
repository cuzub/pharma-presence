<template>
  <Teleport to="body">
    <div v-if="ouvert" class="modal d-block" tabindex="-1" role="dialog" aria-modal="true">
      <div :class="['modal-dialog', 'modal-dialog-scrollable', taille ? `modal-${taille}` : '']" role="document">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ titre }}</h5>
            <button type="button" class="btn-close" aria-label="Fermer" @click="$emit('fermer')"></button>
          </div>
          <div class="modal-body">
            <slot />
          </div>
          <div v-if="$slots.footer" class="modal-footer">
            <slot name="footer" />
          </div>
        </div>
      </div>
    </div>
    <div v-if="ouvert" class="modal-backdrop show" @click="$emit('fermer')"></div>
  </Teleport>
</template>

<script setup>
import { onBeforeUnmount, watch } from 'vue'

const props = defineProps({
  ouvert: { type: Boolean, default: false },
  titre: { type: String, default: '' },
  taille: { type: String, default: '' }
})
const emit = defineEmits(['fermer'])

const surTouche = (event) => {
  if (event.key === 'Escape') emit('fermer')
}

watch(() => props.ouvert, (ouvert) => {
  if (ouvert) window.addEventListener('keydown', surTouche)
  else window.removeEventListener('keydown', surTouche)
}, { immediate: true })

onBeforeUnmount(() => window.removeEventListener('keydown', surTouche))
</script>
