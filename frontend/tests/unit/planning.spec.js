import { describe, expect, it } from 'vitest'
import { demiJourneesDuJour, fondDemiJournee, formatDuree, numeroSemaine, presentsFermeture, sousSeuilFermeture } from '../../src/utils/planning'

describe('planning', () => {
  it('remplit la demi-journée au prorata de la présence', () => {
    // Matin 9h–12h30 (210 min) : arrivée à 10h → blanc sur les 60 premières minutes.
    expect(fondDemiJournee(['10:00', '12:30'], 'matin', '#f00')).toBe(
      'linear-gradient(to right, transparent 28.6%, #f00 28.6%, #f00 100%, transparent 100%)'
    )
    expect(fondDemiJournee(['14:30', '19:30'], 'apres_midi', '#f00')).toContain('#f00 16.7%')
    expect(fondDemiJournee(null, 'matin', '#f00')).toBeNull()
  })

  it('n’affiche pas d’après-midi le samedi', () => {
    expect(demiJourneesDuJour('2025-02-08')).toEqual(['matin'])
    expect(demiJourneesDuJour('2025-02-07')).toEqual(['matin', 'apres_midi'])
  })

  it('compte les présents à la fermeture de chaque demi-journée en excluant les absents', () => {
    const lundi = '2025-02-03'
    const samedi = '2025-02-08'
    const personnes = [
      { planning: { [lundi]: { matin: ['09:00', '12:30'], apres_midi: null } }, absences: [] },
      { planning: { [lundi]: { matin: ['09:00', '12:00'], apres_midi: ['14:30', '19:30'] }, [samedi]: { matin: ['09:00', '12:30'] } }, absences: [] },
      { planning: { [lundi]: { matin: null, apres_midi: ['13:30', '19:00'] }, [samedi]: { matin: ['09:00', '12:00'] } }, absences: [] },
      { planning: { [lundi]: { matin: ['09:00', '12:30'], apres_midi: ['13:30', '19:30'] } }, absences: [{ date_debut: lundi, date_reprise: '2025-02-04' }] },
      { planning: {}, admin: true }
    ]
    expect(presentsFermeture(personnes, lundi, 'matin')).toBe(1)
    expect(presentsFermeture(personnes, lundi, 'apres_midi')).toBe(1)
    expect(presentsFermeture(personnes, samedi, 'matin')).toBe(1)
  })

  it('signale un nombre strictement sous le seuil du jour (semaine / samedi)', () => {
    const seuils = { seuil_semaine: 3, seuil_samedi: 1 }
    expect(sousSeuilFermeture(2, '2025-02-03', seuils)).toBe(true)
    expect(sousSeuilFermeture(3, '2025-02-03', seuils)).toBe(false)
    expect(sousSeuilFermeture(1, '2025-02-08', seuils)).toBe(false)
    expect(sousSeuilFermeture(0, '2025-02-08', seuils)).toBe(true)
    expect(sousSeuilFermeture(0, '2025-02-03', { seuil_semaine: null, seuil_samedi: null })).toBe(false)
  })

  it('formate les durées et numérote les semaines ISO', () => {
    expect(formatDuree(2130)).toBe('35h30')
    expect(formatDuree(0)).toBe('0h')
    expect(numeroSemaine('2025-02-03')).toBe(6)
    expect(numeroSemaine('2026-12-31')).toBe(53)
    expect(numeroSemaine('2027-01-03')).toBe(53)
  })
})
