<template>
  <Teleport to="body">
    <div v-if="active" class="visite" @keydown.esc="fermer" @keydown.right.prevent="suivant" @keydown.left.prevent="precedent">
      <div class="visite-fond" :class="{ 'visite-fond--sombre': !cadre }" @click="fermer"></div>
      <div v-if="cadre" class="visite-cadre" :style="cadre" aria-hidden="true"></div>
      <div
        ref="bulle"
        class="visite-bulle"
        :style="positionBulle"
        role="dialog"
        aria-modal="true"
        aria-labelledby="visite-titre"
        tabindex="-1"
      >
        <div class="small text-muted mb-1">Étape {{ index + 1 }} sur {{ total }}</div>
        <h2 id="visite-titre" class="h6 mb-2">{{ etape.titre }}</h2>
        <p class="mb-3">{{ etape.texte }}</p>
        <div class="d-flex align-items-center gap-2">
          <button type="button" class="btn btn-link btn-sm text-muted p-0 me-auto" @click="fermer">Passer</button>
          <button v-if="index > 0" type="button" class="btn btn-outline-secondary btn-sm" @click="precedent">Précédent</button>
          <button type="button" class="btn btn-primary btn-sm" data-visite-suivant @click="suivant">
            {{ derniere ? 'Terminer' : 'Suivant' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { useVisiteGuidee } from '../composables/useVisiteGuidee'

const { active, etape, index, total, derniere, suivant, precedent, fermer } = useVisiteGuidee()

const MARGE = 6
const ECART = 14
const LARGEUR_BULLE = 340

const bulle = ref(null)
const cadre = ref(null)
const positionBulle = ref({})

// « jour » désigne la case d'aujourd'hui, à défaut la première case cliquable du calendrier.
const trouverCible = (cible) => {
  if (cible === 'jour') {
    return document.querySelector('.calendrier-case.aujourdhui') || document.querySelector('.calendrier-case.cliquable')
  }
  return document.querySelector(`[data-visite="${cible}"]`)
}

const centrer = () => ({ top: '50%', left: '50%', transform: 'translate(-50%, -50%)', width: `${LARGEUR_BULLE}px` })

const placer = (defiler = false) => {
  const cible = etape.value ? trouverCible(etape.value.cible) : null
  if (!cible) {
    cadre.value = null
    positionBulle.value = centrer()
    return
  }
  // « instant » prime sur le défilement animé de Bootstrap : sinon la mesure se fait avant la fin du défilement.
  if (defiler) cible.scrollIntoView({ block: 'center', inline: 'nearest', behavior: 'instant' })
  const r = cible.getBoundingClientRect()
  cadre.value = {
    top: `${r.top - MARGE}px`,
    left: `${r.left - MARGE}px`,
    width: `${r.width + MARGE * 2}px`,
    height: `${r.height + MARGE * 2}px`
  }
  const hauteurBulle = bulle.value?.offsetHeight || 180
  const largeur = Math.min(LARGEUR_BULLE, window.innerWidth - 16)
  const borne = (valeur, max) => Math.max(8, Math.min(valeur, max))
  const haut = borne(r.top + r.height / 2 - hauteurBulle / 2, window.innerHeight - hauteurBulle - 8)
  const gauche = borne(r.left + r.width / 2 - largeur / 2, window.innerWidth - largeur - 8)
  let top
  let left
  if (r.right + ECART + largeur < window.innerWidth) {
    top = haut
    left = r.right + MARGE + ECART
  } else if (r.bottom + ECART + hauteurBulle < window.innerHeight) {
    top = r.bottom + MARGE + ECART
    left = gauche
  } else if (r.top - ECART - hauteurBulle > 0) {
    top = r.top - MARGE - ECART - hauteurBulle
    left = gauche
  } else {
    // Cible trop grande pour laisser de la place : la bulle se pose en bas de l'écran.
    top = window.innerHeight - hauteurBulle - 16
    left = gauche
  }
  positionBulle.value = { top: `${top}px`, left: `${left}px`, width: `${largeur}px` }
}

const actualiser = async () => {
  await nextTick()
  placer(true)
  // Deuxième passage : la hauteur de la bulle n'est connue qu'une fois le texte affiché.
  await nextTick()
  placer()
  bulle.value?.focus({ preventScroll: true })
}

watch([active, index], () => active.value && actualiser(), { flush: 'post' })
const surDefilement = () => active.value && placer()
window.addEventListener('resize', surDefilement)
window.addEventListener('scroll', surDefilement, true)
onBeforeUnmount(() => {
  window.removeEventListener('resize', surDefilement)
  window.removeEventListener('scroll', surDefilement, true)
})
</script>

<style scoped>
.visite {
  position: fixed;
  inset: 0;
  z-index: 2000;
}

/* Bloque les clics hors de la bulle ; le dégradé sombre vient de l'ombre du cadre. */
.visite-fond {
  position: absolute;
  inset: 0;
}

.visite-fond--sombre {
  background: rgba(0, 0, 0, 0.55);
}

.visite-cadre {
  position: fixed;
  border-radius: 10px;
  box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.55);
  outline: 3px solid #fff;
  pointer-events: none;
  transition: all 0.2s ease;
}

.visite-bulle {
  position: fixed;
  padding: 1rem;
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.35);
  outline: none;
  transition: top 0.2s ease, left 0.2s ease;
}
</style>
