<template>
  <article class="carte guide" v-html="contenu"></article>
</template>

<script setup>
import { computed } from 'vue'
import { marked } from 'marked'
import { useAuthStore } from '../stores/auth'
import guideAdmin from '../guide/guide-admin.md?raw'
import guideEmploye from '../guide/guide-employe.md?raw'

const auth = useAuthStore()

const contenu = computed(() => {
  const markdown = auth.estAdmin ? guideAdmin : guideEmploye
  const html = marked.parse(markdown, { async: false })
  return html.replaceAll('src="images/', `src="${import.meta.env.BASE_URL}guide/images/`)
})
</script>

<style scoped>
.guide {
  max-width: 860px;
  margin: 0 auto;
  padding: 2rem;
  line-height: 1.6;
}

.guide :deep(img) {
  display: block;
  max-width: 100%;
  height: auto;
  margin: 1rem 0 1.25rem;
  border: 1px solid var(--bs-border-color);
  border-radius: 0.375rem;
}

.guide :deep(table) {
  display: block;
  overflow-x: auto;
  margin-bottom: 1rem;
}

.guide :deep(th),
.guide :deep(td) {
  padding: 0.35rem 0.6rem;
  border: 1px solid var(--bs-border-color);
}
</style>
