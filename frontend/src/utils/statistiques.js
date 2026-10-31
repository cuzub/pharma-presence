// Données du graphique des heures en plus / en moins (Chart.js), sans dépendance à Vue.

export const MOIS_COURTS = ['Janv.', 'Févr.', 'Mars', 'Avr.', 'Mai', 'Juin', 'Juil.', 'Août', 'Sept.', 'Oct.', 'Nov.', 'Déc.']

// Couleurs distinctes et lisibles sur fond blanc (cyclées si l'équipe est plus grande).
export const PALETTE = [
  '#1f77b4', '#d62728', '#2ca02c', '#9467bd', '#ff7f0e', '#17becf',
  '#8c564b', '#e377c2', '#3f51b5', '#7f7f00', '#00695c', '#b71c1c'
]

// Un employé = un jeu de données : son net mensuel, en heures (positif au-dessus de l'axe, négatif en dessous).
// Pas d'empilement : chaque mois montre une barre par employé, côte à côte.
export const jeuxGraphique = (employes) =>
  employes.map((employe, index) => {
    const couleur = PALETTE[index % PALETTE.length]
    return {
      label: `${employe.prenom} ${employe.nom}`,
      employeId: employe.id,
      data: employe.net.map((m) => m / 60),
      backgroundColor: couleur,
      borderColor: couleur
    }
  })
