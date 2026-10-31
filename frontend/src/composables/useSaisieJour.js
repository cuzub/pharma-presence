import { computed, reactive } from 'vue'

// Clic sur un jour du tableau du mois : heures +/- et déplacement dans le même formulaire.
export const useSaisieJour = ({ employes, recharger }) => {
  const etat = reactive({
    jourOuvert: false,
    employeId: null,
    jour: ''
  })

  const employeDuJour = computed(() => employes.value.find((e) => e.id === etat.employeId) || null)

  const ouvrirJour = (employeId, jour) => {
    Object.assign(etat, { employeId, jour, jourOuvert: true })
  }

  const apresModification = async () => {
    etat.jourOuvert = false
    await recharger()
  }

  return { etat, employeDuJour, ouvrirJour, apresModification }
}
