import { computed, reactive } from 'vue'

// Enchaînement « clic sur un jour → heures / absence » partagé par le tableau du mois et le calendrier.
export const useSaisieJour = ({ employes, recharger }) => {
  const etat = reactive({
    jourOuvert: false,
    employeId: null,
    jour: '',
    absenceOuverte: false,
    absence: null,
    absenceEmployeId: null,
    absenceDebut: ''
  })

  const employeDuJour = computed(() => employes.value.find((e) => e.id === etat.employeId) || null)

  const ouvrirJour = (employeId, jour) => {
    Object.assign(etat, { employeId, jour, jourOuvert: true })
  }

  const nouvelleAbsence = (employeId, jour) => {
    Object.assign(etat, { jourOuvert: false, absence: null, absenceEmployeId: employeId, absenceDebut: jour, absenceOuverte: true })
  }

  const modifierAbsence = (absence) => {
    Object.assign(etat, { jourOuvert: false, absence, absenceEmployeId: absence.employe_id, absenceDebut: '', absenceOuverte: true })
  }

  const apresModification = async () => {
    etat.jourOuvert = false
    etat.absenceOuverte = false
    await recharger()
  }

  return { etat, employeDuJour, ouvrirJour, nouvelleAbsence, modifierAbsence, apresModification }
}
