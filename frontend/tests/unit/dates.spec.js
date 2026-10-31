import { describe, expect, it } from 'vitest'
import {
  absenceBloquanteDuJour, absenceCouvre, ajouterJours, decalerMois, estMoisValide, ferie, formatFr, formatMinutes, jourSemaine, saisieModifiableParEmploye, blocageJourEmploye,
  joursDuMois, libelleMois, minutesRegularisation, paques, titreRegularisation
} from '../../src/utils/dates'

describe('paques', () => {
  it.each([
    [2024, '2024-03-31'],
    [2025, '2025-04-20'],
    [2026, '2026-04-05'],
    [2027, '2027-03-28'],
    [2038, '2038-04-25']
  ])('Pâques %i = %s', (annee, attendu) => {
    expect(paques(annee)).toBe(attendu)
  })
})

describe('jours fériés', () => {
  it('inclut les fêtes fixes', () => {
    expect(ferie('2025-07-14')).toBe('Fête nationale')
    expect(ferie('2025-12-25')).toBe('Noël')
  })

  it('inclut les fêtes mobiles 2025', () => {
    expect(ferie('2025-04-21')).toBe('Lundi de Pâques')
    expect(ferie('2025-05-29')).toBe('Ascension')
    expect(ferie('2025-06-09')).toBe('Lundi de Pentecôte')
  })

  it('ne marque pas un jour ordinaire', () => {
    expect(ferie('2025-04-22')).toBeNull()
  })
})

describe('mois', () => {
  it('liste les jours de février (bissextile ou non)', () => {
    expect(joursDuMois('2025-02')).toHaveLength(28)
    expect(joursDuMois('2024-02')).toHaveLength(29)
    expect(joursDuMois('2025-02')[0]).toBe('2025-02-01')
  })

  it('décale les mois en franchissant les années', () => {
    expect(decalerMois('2025-01', -1)).toBe('2024-12')
    expect(decalerMois('2025-12', 1)).toBe('2026-01')
  })

  it('valide le format', () => {
    expect(estMoisValide('2025-02')).toBe(true)
    expect(estMoisValide('2025-13')).toBe(false)
    expect(estMoisValide('abc')).toBe(false)
  })

  it('formate en français', () => {
    expect(libelleMois('2025-08')).toBe('août 2025')
    expect(formatFr('2025-02-03')).toBe('03/02/2025')
  })

  it('calcule le jour de la semaine (lundi = 0)', () => {
    expect(jourSemaine('2025-02-03')).toBe(0)
    expect(jourSemaine('2025-02-09')).toBe(6)
  })

  it('ajoute des jours sans décalage horaire (changement d’heure)', () => {
    expect(ajouterJours('2025-03-29', 2)).toBe('2025-03-31')
    expect(ajouterJours('2025-10-25', 2)).toBe('2025-10-27')
  })
})

describe('absenceCouvre', () => {
  const absence = { date_debut: '2025-01-28', date_reprise: '2025-02-03' }

  it('couvre du premier jour au jour de reprise exclu', () => {
    expect(absenceCouvre(absence, '2025-01-28')).toBe(true)
    expect(absenceCouvre(absence, '2025-02-02')).toBe(true)
    expect(absenceCouvre(absence, '2025-02-03')).toBe(false)
    expect(absenceCouvre(absence, '2025-01-27')).toBe(false)
  })

  it('gère les absences en cours', () => {
    expect(absenceCouvre({ date_debut: '2025-02-01', date_reprise: null }, '2030-01-01')).toBe(true)
  })
})

describe('absenceBloquanteDuJour', () => {
  const conge = { motif_libelle: 'Congé', motif_bloque_saisie: true, date_debut: '2025-01-28', date_reprise: '2025-02-03' }
  const formation = { motif_libelle: 'Formation', motif_bloque_saisie: false, date_debut: '2025-02-10', date_reprise: null }

  it('renvoie l’absence dont le motif bloque la saisie le jour concerné', () => {
    expect(absenceBloquanteDuJour([conge], '2025-01-30')).toBe(conge)
  })

  it('ignore les absences dont le motif ne bloque pas la saisie', () => {
    expect(absenceBloquanteDuJour([formation], '2025-02-11')).toBeNull()
  })

  it('renvoie null hors de l’absence', () => {
    expect(absenceBloquanteDuJour([conge], '2025-02-03')).toBeNull()
    expect(absenceBloquanteDuJour([], '2025-02-03')).toBeNull()
  })
})

describe('formatMinutes', () => {
  it.each([
    [90, '+1h30'],
    [15, '+15min'],
    [-30, '-30min'],
    [120, '+2h'],
    [-65, '-1h05'],
    [0, ''],
    [null, '']
  ])('%s → %s', (minutes, attendu) => {
    expect(formatMinutes(minutes)).toBe(attendu)
  })
})

describe('saisieModifiableParEmploye', () => {
  it.each([
    ['2025-03-05', '2025-02-28', true],
    ['2025-03-06', '2025-02-28', false],
    ['2025-03-06', '2025-03-31', true],
    ['2025-03-01', '2025-01-31', false],
    ['2025-03-01', '2025-04-01', false],
    ['2025-01-03', '2024-12-15', true]
  ])('le %s, déplacement du %s → %s', (reference, jour, attendu) => {
    expect(saisieModifiableParEmploye(jour, reference)).toBe(attendu)
  })
})

describe('régularisations', () => {
  it.each([
    ['credit', 2, 30, 150],
    ['debit', 20, 0, -1200],
    ['debit', '', 45, -45],
    ['credit', 0, 0, null],
    ['credit', 1, 60, null],
    ['credit', -1, 0, null],
    ['credit', 1.5, 0, null]
  ])('%s de %sh%s → %s', (sens, heures, minutes, attendu) => {
    expect(minutesRegularisation(sens, heures, minutes)).toBe(attendu)
  })

  it('titre avec et sans commentaire', () => {
    expect(titreRegularisation({ minutes: -1200, commentaire: 'Heures payées' })).toBe('Régularisation -20h — Heures payées')
    expect(titreRegularisation({ minutes: 90, commentaire: null })).toBe('Régularisation +1h30')
  })
})

describe('blocageJourEmploye', () => {
  const reference = '2025-05-12'
  it.each([
    ['2025-05-13', 'future'],
    ['2025-05-10', null],
    ['2025-05-04', 'dimanche'],
    ['2025-05-08', 'ferie'],
    ['2025-05-06', null]
  ])('%s → %s', (jour, attendu) => {
    expect(blocageJourEmploye(jour, [], reference)).toBe(attendu)
  })

  it('bloque les jours de fermeture de la pharmacie', () => {
    expect(blocageJourEmploye('2025-05-06', [{ date: '2025-05-06' }], reference)).toBe('fermeture')
  })
})
