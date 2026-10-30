import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import Calendrier from '../../src/components/Calendrier.vue'

const absence = {
  id: 1,
  date_debut: '2025-01-28',
  date_reprise: '2025-02-03',
  motif_libelle: 'Congés payés',
  motif_couleur: '#0d6efd'
}

const monter = (props = {}) => mount(Calendrier, { props: { mois: '2025-02', absences: [absence], ...props } })

describe('Calendrier', () => {
  it('commence le mois sur le bon jour de la semaine', () => {
    // Le 1er février 2025 est un samedi : 5 cases vides avant.
    expect(monter().findAll('.calendrier-case.vide')).toHaveLength(5)
    expect(monter().findAll('[data-jour]')).toHaveLength(28)
  })

  it("affiche l'absence jusqu'à la veille du jour de reprise", () => {
    const wrapper = monter()
    expect(wrapper.find('[data-jour="2025-02-02"]').text()).toContain('Congés payés')
    expect(wrapper.find('[data-jour="2025-02-03"]').text()).not.toContain('Congés payés')
  })

  it('affiche les heures en plus, les dimanches et les fermetures', () => {
    const wrapper = monter({ heures: { '2025-02-04': 1.5 }, joursFermeture: [{ date: '2025-02-10', libelle: 'Inventaire' }] })
    expect(wrapper.find('[data-jour="2025-02-04"]').text()).toContain('+1,5 h')
    expect(wrapper.find('[data-jour="2025-02-09"]').classes()).toContain('dimanche')
    expect(wrapper.find('[data-jour="2025-02-10"]').text()).toContain('Inventaire')
  })

  it('hachure les jours hors contrat', () => {
    const wrapper = monter({ contrats: [{ date_debut: '2025-02-10', date_fin: null }] })
    expect(wrapper.find('[data-jour="2025-02-09"]').classes()).toContain('hors-contrat')
    expect(wrapper.find('[data-jour="2025-02-10"]').classes()).not.toContain('hors-contrat')
  })

  it('émet le jour cliqué, sauf en lecture seule', async () => {
    const editable = monter()
    await editable.find('[data-jour="2025-02-12"]').trigger('click')
    expect(editable.emitted('choisir-jour')).toEqual([['2025-02-12']])

    const lecture = monter({ lectureSeule: true })
    expect(lecture.find('button[data-jour]').exists()).toBe(false)
    await lecture.find('[data-jour="2025-02-12"]').trigger('click')
    expect(lecture.emitted('choisir-jour')).toBeUndefined()
  })

  it('signale les jours fériés mobiles', () => {
    expect(mount(Calendrier, { props: { mois: '2025-06' } }).find('[data-jour="2025-06-09"]').text()).toContain('Lundi de Pentecôte')
  })
})
