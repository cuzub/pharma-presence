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

  // Régularisation depuis Employés → Heures +/- : 2 h payées (retirées du compteur), visible dans le tableau et comptée dans le solde.
  await page.goto('/employes')
  await page.locator('tr', { hasText: nom }).getByRole('button', { name: 'Heures +/-' }).click()
  await page.locator('[data-sens="debit"]').click()
  await expect(page.locator('[data-sens="debit"]')).toHaveAttribute('aria-pressed', 'true')
  await page.selectOption('#hpm-heures', '2')
  await page.fill('#hpm-jour', `${mois}-06`)
  await page.fill('#hpm-commentaire', 'Heures payées e2e')
  await expect(page.locator('[data-apercu]')).toContainText('-1h')
  await page.locator('[data-form-regularisation] button[type=submit]').click()
  await expect(page.locator('tr[data-regularisation]')).toContainText('-2h')
  await page.keyboard.press('Escape')
  await expect(page.locator('tr', { hasText: nom })).toContainText('-1h')
  await page.goto(`/?mois=${mois}`)
  await expect(ligne.locator(`td[data-jour="${mois}-06"] [data-regularisation]`)).toHaveText('-2h')
  await expect(ligne.locator(`td[data-jour="${mois}-06"]`)).toHaveAttribute('title', /Heures payées e2e/)
  await expect(ligne.locator('td[data-solde]')).toHaveText('-1h')

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
  // La régularisation apparaît dans le calendrier de l'employé (lecture seule), avec le solde cumulé.
  await expect(page.locator(`[data-jour="${mois}-06"] [data-regularisation]`)).toContainText('-2h')
  await expect(page.locator('[data-solde]')).toHaveText('-1h')

  await page.goto('/employes')
  await expect(page).toHaveURL(/\/mon-mois/)

  // L'employé saisit ses heures +/- depuis le calendrier (clic sur la date).
  await page.locator(`[data-jour="${mois}-04"]`).click()
  await page.fill('#jour-minutes', '45')
  await page.locator('.modal-body form button[type=submit]').click()
  await expect(page.locator(`[data-jour="${mois}-04"] .badge`)).toHaveText('+45min')

  // Clic sur la date → choix du motif : les km sont remplis automatiquement.
  await page.locator(`[data-jour="${mois}-03"]`).click()
  await page.getByRole('button', { name: 'Ajouter un déplacement' }).click()
  await page.selectOption('#dep-motif', { label: `${destination} — 7 km` })
  await expect(page.locator('#dep-km')).toHaveValue('7')
  await page.click('button[form=form-deplacement]')
  await expect(page.locator(`[data-jour="${mois}-03"] [data-deplacement]`)).toContainText('7 km')

  // Motif « Autre » : distance et précision libres.
  await page.locator(`[data-jour="${mois}-02"]`).click()
  await page.getByRole('button', { name: 'Ajouter un déplacement' }).click()
  await page.selectOption('#dep-motif', 'autre')
  await page.fill('#dep-precision', 'Test e2e')
  await page.fill('#dep-km', '12')
  await page.click('button[form=form-deplacement]')
  const autre = page.locator(`[data-jour="${mois}-02"] [data-deplacement]`)
  await expect(autre).toContainText('12 km')

  // Correction avec le crayon, depuis le modal du jour.
  await page.locator(`[data-jour="${mois}-02"]`).click()
  await page.locator('.modal.d-block').getByRole('button', { name: /Modifier le déplacement/ }).click()
  await page.fill('#dep-km', '12.5')
  await page.click('button[form=form-deplacement]')
  await expect(autre).toContainText('12,5 km')
  await deconnecter(page)

  // 4. La pharmacienne voit les déplacements (déclaratifs, sans validation), l'historique, puis exporte.
  await connecter(page, ADMIN, ADMIN_MDP)
  await page.goto(`/?mois=${mois}`)
  await expect(page.locator('tr', { hasText: nom }).first()).toContainText('12,5 km')

  await page.goto('/historique')
  await page.selectOption('#h-employe', { label: `${nom} Test` })
  await page.selectOption('#h-auteur', 'employe')
  const journal = page.locator('tr[data-journal]')
  await expect(journal).toHaveCount(4)
  await expect(journal.first()).toContainText('Modification')
  await expect(journal.first()).toContainText('12,5 km')
  await page.selectOption('#h-auteur', 'admin')
  await page.selectOption('#h-type', 'heures')
  await expect(journal).toHaveCount(2)
  await expect(journal.first()).toContainText('-30min')

  // Statistiques : net mensuel de l'employé (+90, -30, +45 et la régularisation de -2h = -15min), puis année précédente.
  await page.goto('/statistiques')
  await expect(page.getByRole('heading', { name: 'Statistiques — heures en plus / en moins' })).toBeVisible()
  await expect(page.locator('tr', { hasText: nom }).locator('td.col-total')).toHaveText('-15min')
  await page.getByRole('button', { name: 'Année précédente' }).click()
  await expect(page).toHaveURL(new RegExp(`annee=${new Date().getFullYear() - 1}`))

  await page.goto(`/export?mois=${mois}`)
  const apercu = page.locator('tr', { hasText: nom })
  await expect(apercu).toContainText('19,5')
  await expect(apercu).not.toContainText('Entrée')
  await expect(page.getByRole('button', { name: /Détail des heures/ })).toHaveCount(0)
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

test('absence bloquante : conflit signalé, suppression confirmée, saisie refusée ensuite', async ({ page }) => {
  const nom = `ABS${Date.now().toString(36)}`.toUpperCase()
  const mois = new Date().toISOString().slice(0, 7)
  const mm = mois.slice(5, 7)

  await connecter(page, ADMIN, ADMIN_MDP)
  await page.goto('/employes')
  await page.getByRole('button', { name: 'Nouvel employé' }).click()
  await page.fill('#c-nom', nom)
  await page.fill('#c-prenom', 'Absent')
  await page.fill('#c-entree', `${mois}-01`)
  await page.fill('#c-heures', '151.67')
  await page.click('button[form=form-creation]')
  await expect(page.getByText('Compte créé')).toBeVisible()
  await page.keyboard.press('Escape')

  // Des heures sont saisies le 10 ; une absence de congés du 8 au 13 les rendrait incohérentes.
  await page.goto(`/?mois=${mois}`)
  const ligne = page.locator('tr', { hasText: nom })
  await ligne.locator(`td[data-jour="${mois}-10"]`).click()
  await page.fill('#jour-minutes', '30')
  await page.locator('.modal-body form button[type=submit]').click()
  await expect(ligne.locator(`td[data-jour="${mois}-10"]`)).toHaveText('+30min')

  await ligne.locator(`td[data-jour="${mois}-08"]`).click()
  await page.getByRole('button', { name: 'Déclarer une absence à partir de ce jour' }).click()
  await page.selectOption('#absence-motif', { label: 'Congés payés' })
  await page.fill('#absence-reprise', `${mois}-13`)
  await page.click('button[form=form-absence]')

  // Le serveur refuse tant que la suppression n'est pas confirmée, et liste les saisies concernées.
  await expect(page.locator('.alert-danger').first()).toContainText(`10/${mm} : +30min`)
  await page.getByRole('button', { name: "Supprimer ces saisies et enregistrer l'absence" }).click()
  await expect(page.locator('#form-absence')).toHaveCount(0)

  await expect(ligne.locator(`td[data-jour="${mois}-10"]`)).not.toHaveText('+30min')
  await expect(ligne.locator(`td[data-jour="${mois}-09"] .code-absence`)).toHaveText('CP')

  // Un jour d'absence bloquante ne peut plus recevoir d'heures ni de déplacement.
  await ligne.locator(`td[data-jour="${mois}-09"]`).click()
  await expect(page.locator('[data-jour-bloque]')).toContainText('saisie impossible')
  await expect(page.locator('#jour-minutes')).toBeDisabled()
  await expect(page.getByRole('button', { name: 'Ajouter un déplacement' })).toBeDisabled()
  await page.keyboard.press('Escape')
  await expect(page.locator('.modal.d-block')).toHaveCount(0)
  await deconnecter(page)
})

test('statistiques : isolement d’un employé depuis le tableau', async ({ page }) => {
  await connecter(page, ADMIN, ADMIN_MDP)
  await page.goto('/statistiques')
  await page.locator('tbody tr[role=button]').first().click()
  await expect(page.locator('tbody tr.table-active')).toHaveCount(1)
  await page.locator('tbody tr.table-active').click()
  await expect(page.locator('tbody tr.table-active')).toHaveCount(0)
})
