import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import AnneeNavigateur from '../../src/components/AnneeNavigateur.vue'
import { anneeCourante } from '../../src/utils/dates'

describe('AnneeNavigateur', () => {
  it('émet l’année précédente et suivante (±1)', async () => {
    const wrapper = mount(AnneeNavigateur, { props: { modelValue: 2025 } })
    expect(wrapper.text()).toContain('2025')

    await wrapper.get('button[aria-label="Année précédente"]').trigger('click')
    await wrapper.get('button[aria-label="Année suivante"]').trigger('click')
    expect(wrapper.emitted('update:modelValue')).toEqual([[2024], [2026]])
  })

  it('le bouton « année en cours » ne s’affiche qu’hors année en cours, sans décaler les flèches', async () => {
    const autre = mount(AnneeNavigateur, { props: { modelValue: 2020 } })
    const bouton = autre.get('button[aria-label="Revenir à l\'année en cours"]')
    expect(bouton.classes()).not.toContain('invisible')
    expect(bouton.attributes('title')).toContain(String(anneeCourante()))
    await bouton.trigger('click')
    expect(autre.emitted('update:modelValue')).toEqual([[anneeCourante()]])

    const courante = mount(AnneeNavigateur, { props: { modelValue: anneeCourante() } })
    // Toujours présent (place réservée), mais invisible et hors tabulation.
    const cache = courante.get('button[aria-label="Revenir à l\'année en cours"]')
    expect(cache.classes()).toContain('invisible')
    expect(cache.attributes('tabindex')).toBe('-1')
  })
})
