import { describe, expect, it } from 'vitest'
import { PALETTE, jeuxGraphique } from '../../src/utils/statistiques'

const employe = (id, prenom, nom, net) => ({ id, prenom, nom, net })

const vide = Array(12).fill(0)
const alice = employe(1, 'Alice', 'Martin', [90, -90, ...vide.slice(2)])
const bruno = employe(2, 'Bruno', 'Dupont', vide)

describe('jeuxGraphique', () => {
  it('crée un seul jeu par employé, en net, empilé', () => {
    const jeux = jeuxGraphique([alice, bruno])
    expect(jeux).toHaveLength(2)
    expect(jeux.every((j) => j.stack === 'heures')).toBe(true)
    expect(jeux[0].backgroundColor).not.toBe(jeux[1].backgroundColor)
  })

  it('nomme le jeu « Prénom Nom » et identifie l’employé', () => {
    const [jeu] = jeuxGraphique([alice])
    expect(jeu.label).toBe('Alice Martin')
    expect(jeu.employeId).toBe(1)
  })

  it('convertit le net mensuel en heures, positif et négatif', () => {
    const [jeu] = jeuxGraphique([alice])
    expect(jeu.data).toEqual([1.5, -1.5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
  })

  it('cycle la palette quand il y a plus d’employés que de couleurs', () => {
    const equipe = Array.from({ length: PALETTE.length + 1 }, (_, i) => employe(i, 'P', `N${i}`, vide))
    const jeux = jeuxGraphique(equipe)
    expect(jeux[jeux.length - 1].backgroundColor).toBe(PALETTE[0])
    expect(new Set(PALETTE).size).toBe(PALETTE.length)
    expect(PALETTE.length).toBeGreaterThanOrEqual(10)
  })

  it('renvoie une liste vide sans employé', () => {
    expect(jeuxGraphique([])).toEqual([])
  })
})
