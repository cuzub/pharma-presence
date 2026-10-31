import { describe, expect, it } from 'vitest'
import { PALETTE, jeuxGraphique } from '../../src/utils/statistiques'

const employe = (id, prenom, nom, plus, moins) => ({ id, prenom, nom, plus, moins, net: plus.map((p, i) => p + moins[i]) })

const vide = Array(12).fill(0)
const alice = employe(1, 'Alice', 'Martin', [90, ...vide.slice(1)], [-30, -60, ...vide.slice(2)])
const bruno = employe(2, 'Bruno', 'Dupont', vide, vide)

describe('jeuxGraphique', () => {
  it('crée deux jeux par employé, empilés, de même couleur', () => {
    const jeux = jeuxGraphique([alice, bruno])
    expect(jeux).toHaveLength(4)
    expect(jeux.map((j) => j.sens)).toEqual(['plus', 'moins', 'plus', 'moins'])
    expect(jeux.every((j) => j.stack === 'heures')).toBe(true)
    expect(jeux[0].backgroundColor).toBe(jeux[1].backgroundColor)
    expect(jeux[0].backgroundColor).not.toBe(jeux[2].backgroundColor)
  })

  it('nomme chaque jeu « Prénom Nom » et identifie l’employé', () => {
    const jeux = jeuxGraphique([alice])
    expect(jeux.map((j) => j.label)).toEqual(['Alice Martin', 'Alice Martin'])
    expect(jeux.map((j) => j.employeId)).toEqual([1, 1])
  })

  it('convertit les minutes en heures', () => {
    const [plus, moins] = jeuxGraphique([alice])
    expect(plus.data).toEqual([1.5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    expect(moins.data[0]).toBe(-0.5)
    expect(moins.data[1]).toBe(-1)
  })

  it('cycle la palette quand il y a plus d’employés que de couleurs', () => {
    const equipe = Array.from({ length: PALETTE.length + 1 }, (_, i) => employe(i, 'P', `N${i}`, vide, vide))
    const jeux = jeuxGraphique(equipe)
    expect(jeux[jeux.length - 2].backgroundColor).toBe(PALETTE[0])
    expect(new Set(PALETTE).size).toBe(PALETTE.length)
    expect(PALETTE.length).toBeGreaterThanOrEqual(10)
  })

  it('renvoie une liste vide sans employé', () => {
    expect(jeuxGraphique([])).toEqual([])
  })
})
