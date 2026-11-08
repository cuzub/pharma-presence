import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it } from 'vitest'
import Guide from '../../src/views/Guide.vue'
import { useAuthStore } from '../../src/stores/auth'

function monter(role) {
  const auth = useAuthStore()
  auth.utilisateur = { role, prenom: 'Test', nom: 'Test', identifiant: 'test' }
  return mount(Guide)
}

describe('page du guide utilisateur', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('affiche le guide administrateur pour un admin', () => {
    const wrapper = monter('admin')
    expect(wrapper.find('h1').text()).toBe("Guide d'utilisation")
    expect(wrapper.text()).toContain('Statistiques')
    expect(wrapper.text()).not.toContain('Votre espace est la page')
    expect(wrapper.find('img').attributes('src')).toMatch(/guide\/images\/admin-/)
  })

  it('affiche le guide employé pour un employé', () => {
    const wrapper = monter('employe')
    expect(wrapper.find('h1').text()).toBe("Guide d'utilisation")
    expect(wrapper.text()).toContain('Votre espace est la page')
    expect(wrapper.text()).not.toContain('Statistiques')
    expect(wrapper.find('img').attributes('src')).toMatch(/guide\/images\/employe-/)
  })
})
