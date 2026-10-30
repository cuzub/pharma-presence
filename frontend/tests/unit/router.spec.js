import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it } from 'vitest'
import { garde } from '../../src/router'
import { useAuthStore } from '../../src/stores/auth'

const connecter = (utilisateur) => {
  const auth = useAuthStore()
  auth.sessionChargee = true
  auth.utilisateur = utilisateur
}

const route = (path, meta = {}) => ({ path, fullPath: path, meta })

describe('garde du routeur', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('renvoie vers la connexion sans session', async () => {
    connecter(null)
    expect(await garde(route('/absences', { role: 'admin' }))).toEqual({ path: '/login', query: { redirect: '/absences' } })
  })

  it('impose le changement de mot de passe provisoire', async () => {
    connecter({ role: 'employe', doit_changer_mdp: true })
    expect(await garde(route('/mon-mois', { role: 'employe' }))).toBe('/mot-de-passe')
    expect(await garde(route('/mot-de-passe', { mdpProvisoireAutorise: true }))).toBe(true)
  })

  it('interdit les pages de la pharmacienne aux employés', async () => {
    connecter({ role: 'employe', doit_changer_mdp: false })
    expect(await garde(route('/employes', { role: 'admin' }))).toBe('/mon-mois')
    expect(await garde(route('/mon-mois', { role: 'employe' }))).toBe(true)
  })

  it("renvoie la pharmacienne vers son tableau si elle ouvre une page d'employé", async () => {
    connecter({ role: 'admin', doit_changer_mdp: false })
    expect(await garde(route('/mon-mois', { role: 'employe' }))).toBe('/')
    expect(await garde(route('/export', { role: 'admin' }))).toBe(true)
  })

  it('redirige une personne connectée hors de la page de connexion', async () => {
    connecter({ role: 'admin', doit_changer_mdp: false })
    expect(await garde(route('/login', { public: true }))).toBe('/')
  })
})
