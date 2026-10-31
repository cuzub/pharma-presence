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

test('arrivée d’un employé, heures +/-, déplacements déclaratifs, historique et export comptable', async ({ page }) => {
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

  // 2. La pharmacienne saisit des minutes en plus et en moins depuis le tableau du mois.
  await page.goto(`/?mois=${mois}`)
  const ligne = page.locator('tr', { hasText: nom })
  await ligne.locator(`td[data-jour="${mois}-02"]`).click()
  await page.fill('#jour-minutes', '90')
  await page.locator('.modal-body form button[type=submit]').click()
  await expect(ligne.locator(`td[data-jour="${mois}-02"]`)).toHaveText('+1h30')
  await ligne.locator(`td[data-jour="${mois}-05"]`).click()
  await page.fill('#jour-minutes', '-30')
  await page.locator('.modal-body form button[type=submit]').click()
  await expect(ligne.locator(`td[data-jour="${mois}-05"]`)).toHaveText('-30min')
  await expect(ligne.locator('td.col-total').first()).toHaveText('+1h')

  // La pharmacienne crée un motif de déplacement avec sa distance.
  const destination = `Dest${suffixe}`
  await page.goto('/parametres')
  await page.fill('#md-libelle', destination)
  await page.fill('#md-km', '7')
  await page.locator('form', { has: page.locator('#md-libelle') }).getByRole('button', { name: 'Ajouter' }).click()
  await expect(page.locator(`input[aria-label=Motif]`).last()).toHaveValue(destination)
  await deconnecter(page)

  // 3. L'employé se connecte, doit changer son mot de passe, puis déclare un déplacement.
  await connecter(page, identifiant, motDePasseProvisoire)
  await expect(page).toHaveURL(/\/mot-de-passe/)
  await page.fill('#actuel', motDePasseProvisoire)
  await page.fill('#nouveau', 'mot-de-passe-e2e-solide')
  await page.fill('#confirmation', 'mot-de-passe-e2e-solide')
  await page.click('button[type=submit]')
  await expect(page).toHaveURL(/\/mon-mois/)
  await expect(page.locator(`[data-jour="${mois}-02"] .badge`)).toHaveText('+1h30')

  await page.goto('/employes')
  await expect(page).toHaveURL(/\/mon-mois/)

  // Clic sur la date → choix du motif : les km sont remplis automatiquement.
  await page.locator(`[data-jour="${mois}-03"]`).click()
  await page.selectOption('#dep-motif', { label: `${destination} — 7 km` })
  await expect(page.locator('#dep-km')).toHaveValue('7')
  await page.click('button[form=form-deplacement]')
  await expect(page.locator(`[data-jour="${mois}-03"] [data-deplacement]`)).toContainText('7 km')

  // Motif « Autre » : distance et précision libres.
  await page.locator(`[data-jour="${mois}-02"]`).click()
  await page.selectOption('#dep-motif', 'autre')
  await page.fill('#dep-precision', 'Test e2e')
  await page.fill('#dep-km', '12')
  await page.click('button[form=form-deplacement]')
  const autre = page.locator(`[data-jour="${mois}-02"] [data-deplacement]`)
  await expect(autre).toContainText('12 km')

  // Correction avec le crayon.
  await autre.getByRole('button', { name: /Modifier/ }).click()
  await page.fill('#dep-km', '12.5')
  await page.click('button[form=form-deplacement]')
  await expect(autre).toContainText('12,5 km')
  await deconnecter(page)

  // 4. La pharmacienne voit les déplacements (déclaratifs, sans validation), l'historique, puis exporte.
  await connecter(page, ADMIN, ADMIN_MDP)
  await page.goto(`/deplacements?mois=${mois}`)
  await expect(page.locator('tr', { hasText: nom })).toHaveCount(2)

  await page.goto('/historique')
  await page.selectOption('#h-employe', { label: `${nom} Test` })
  await page.selectOption('#h-auteur', 'employe')
  const journal = page.locator('tr[data-journal]')
  await expect(journal).toHaveCount(3)
  await expect(journal.first()).toContainText('Modification')
  await expect(journal.first()).toContainText('12,5 km')
  await page.selectOption('#h-auteur', 'admin')
  await page.selectOption('#h-type', 'heures')
  await expect(journal).toHaveCount(2)
  await expect(journal.first()).toContainText('-30min')

  // Statistiques : cumul mensuel net de l'employé (+90 et -30 ce mois-ci = +1h), puis année précédente.
  await page.goto('/statistiques')
  await expect(page.getByRole('heading', { name: 'Statistiques — heures en plus / en moins' })).toBeVisible()
  await expect(page.locator('tr', { hasText: nom }).locator('td.col-total')).toHaveText('+1h')
  await page.getByRole('button', { name: 'Année précédente' }).click()
  await expect(page).toHaveURL(new RegExp(`annee=${new Date().getFullYear() - 1}`))

  await page.goto(`/export?mois=${mois}`)
  const apercu = page.locator('tr', { hasText: nom })
  await expect(apercu).toContainText('19,5')
  await expect(apercu.locator('td').nth(3)).toHaveText('60')
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
