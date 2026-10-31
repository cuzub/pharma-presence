// Bulle d'aide immédiate (sans délai), multi-lignes, qui suit la cellule survolée.
// La valeur peut être une chaîne ou un tableau de lignes ; la première ligne est mise en avant.

let bulle = null
let source = null

const retirer = () => {
  bulle?.remove()
  bulle = null
  source = null
}

const lignesDe = (valeur) => (Array.isArray(valeur) ? valeur : [valeur]).filter(Boolean)

const remplir = (lignes) => {
  bulle.replaceChildren(
    ...lignes.map((texte, index) => {
      const ligne = document.createElement('div')
      ligne.textContent = texte
      if (index === 0) ligne.className = 'infobulle-titre'
      return ligne
    })
  )
}

const placer = (el) => {
  const cible = el.getBoundingClientRect()
  const taille = bulle.getBoundingClientRect()
  let haut = cible.top - taille.height - 8
  if (haut < 4) haut = cible.bottom + 8
  const gauche = Math.min(Math.max(4, cible.left + cible.width / 2 - taille.width / 2), window.innerWidth - taille.width - 4)
  bulle.style.top = `${haut}px`
  bulle.style.left = `${gauche}px`
}

const afficher = (el) => {
  const lignes = lignesDe(el._infobulle)
  if (!lignes.length) return retirer()
  if (!bulle) {
    bulle = document.createElement('div')
    bulle.className = 'infobulle'
    bulle.setAttribute('role', 'tooltip')
    document.body.appendChild(bulle)
  }
  source = el
  remplir(lignes)
  placer(el)
}

// Une bulle ouverte ne doit pas rester affichée quand la page défile.
window.addEventListener('scroll', retirer, { capture: true, passive: true })

export const infobulle = {
  mounted(el, { value }) {
    el._infobulle = value
    el.addEventListener('mouseenter', () => afficher(el))
    el.addEventListener('mouseleave', retirer)
  },
  updated(el, { value }) {
    el._infobulle = value
    if (source === el) afficher(el)
  },
  beforeUnmount(el) {
    if (source === el) retirer()
  }
}
