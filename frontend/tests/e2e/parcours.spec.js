import { expect, test } from '@playwright/test'

const ADMIN = process.env.E2E_ADMIN || 'admin'
const ADMIN_MDP = process.env.E2E_ADMIN_MDP || 'admin-demo-1234'

const connecter = async (page, identifiant, motDePasse, { attendreSucces = true } = {}) => {
  await page.goto('/login')
  await page.fill('#identifiant', identifiant)
  await page.fill('#mot-de-passe', motDePasse)
  await page.click('button[type=submit]')
  if (attendreSucces) await page.waitForURL((url) => !url.pathname.startsWith('/login'))
}

const deconnecter = async (page) => {
  await page.getByRole('button', { name: 'Déconnexion' }).click()
  await expect(page).toHaveURL(/\/login/)
}

test('arrivée d’un employé, déclaration d’un déplacement et export comptable', async ({ page }) => {
  const suffixe = Date.now().toString(36)
  const nom = `E2E${suffixe}`.toUpperCase()
  const mois = new Date().toISOString().slice(0, 7)

  // 1. La pharmacienne crée le compte du nouvel employé.
  await connecter(page, ADMIN, ADMIN_MDP)
  await expect(page.getByRole('heading', { name: 'Tableau du mois' })).toBeVisible()
  await page.goto('/employes')
  await page.getByRole('button', { name: 'Nouvel employé' }).click()
  await page.fill('#c-nom', nom)
  await page.fill('#c-prenom', 'Test')
  await page.fill('#c-entree', `${mois}-01`)
  await page.fill('#c-heures', '121.33')
  const identifiant = await page.inputValue('#c-identifiant')
  const motDePasseProvisoire = await page.inputValue('#c-mdp')
  await page.click('button[form=form-creation]')
  await expect(page.getByText('Compte créé')).toBeVisible()
  await page.keyboard.press('Escape')

  // 2. La pharmacienne saisit des heures en plus depuis le tableau du mois.
  await page.goto(`/?mois=${mois}`)
  const ligne = page.locator('tr', { hasText: nom })
  await ligne.locator(`td[data-jour="${mois}-02"]`).click()
  await page.fill('#jour-heures', '1.5')
  await page.locator('.modal-body form button[type=submit]').click()
  await expect(ligne.locator(`td[data-jour="${mois}-02"]`)).toHaveText('+1,5')
  await deconnecter(page)

  // 3. L'employé se connecte, doit changer son mot de passe, puis déclare un déplacement.
  await connecter(page, identifiant, motDePasseProvisoire)
  await expect(page).toHaveURL(/\/mot-de-passe/)
  await page.fill('#actuel', motDePasseProvisoire)
  await page.fill('#nouveau', 'mot-de-passe-e2e-solide')
  await page.fill('#confirmation', 'mot-de-passe-e2e-solide')
  await page.click('button[type=submit]')
  await expect(page).toHaveURL(/\/mon-mois/)
  await expect(page.getByText('+1,5 h').first()).toBeVisible()

  await page.goto('/employes')
  await expect(page).toHaveURL(/\/mon-mois/)

  await page.goto('/mes-deplacements')
  await page.getByRole('button', { name: 'Déclarer un déplacement' }).click()
  await page.fill('#dep-date', `${mois}-02`)
  await page.fill('#dep-km', '12.5')
  await page.fill('#dep-depart', 'Pharmacie')
  await page.fill('#dep-arrivee', 'Grossiste')
  await page.fill('#dep-motif', 'Test e2e')
  await page.click('button[form=form-deplacement]')
  await expect(page.getByText('En attente')).toBeVisible()
  await deconnecter(page)

  // 4. La pharmacienne voit l'export bloqué, valide le déplacement, puis exporte.
  await connecter(page, ADMIN, ADMIN_MDP)
  await page.goto(`/export?mois=${mois}`)
  await expect(page.getByText(`Test ${nom} : 1 déplacement(s) en attente de validation`)).toBeVisible()

  await page.goto('/deplacements')
  const deplacement = page.locator('tr', { hasText: nom })
  await deplacement.getByRole('button', { name: 'Valider' }).click()
  await expect(deplacement).toHaveCount(0)

  // Les déplacements de démonstration éventuellement en attente sont aussi validés pour débloquer l'export.
  while (await page.locator('tbody tr button.btn-success').count()) {
    await page.locator('tbody tr button.btn-success').first().click()
    await page.waitForTimeout(300)
  }

  await page.goto(`/export?mois=${mois}`)
  await expect(page.locator('tr', { hasText: nom })).toContainText('12,5')
  const [telechargement] = await Promise.all([
    page.waitForEvent('download'),
    page.getByRole('button', { name: /État préparatoire Excel/ }).click()
  ])
  expect(telechargement.suggestedFilename()).toBe(`etat-preparatoire-${mois}.xlsx`)

  // 5. Départ de l'employé : son compte est désactivé.
  await page.goto('/employes')
  await page.locator('tr', { hasText: nom }).getByRole('button', { name: 'Gérer' }).click()
  page.once('dialog', (dialog) => dialog.accept())
  await page.getByRole('button', { name: 'Enregistrer le départ' }).click()
  await expect(page.getByText('Départ enregistré, compte désactivé.')).toBeVisible()
  await page.keyboard.press('Escape')
  await deconnecter(page)

  await connecter(page, identifiant, 'mot-de-passe-e2e-solide', { attendreSucces: false })
  await expect(page.getByText('Identifiant ou mot de passe incorrect')).toBeVisible()
})
