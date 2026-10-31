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

  it('propose « Cette année » seulement hors année en cours', () => {
    expect(mount(AnneeNavigateur, { props: { modelValue: 2020 } }).text()).toContain('Cette année')
    const courante = anneeCourante()
    expect(mount(AnneeNavigateur, { props: { modelValue: courante } }).text()).not.toContain('Cette année')
  })
})
