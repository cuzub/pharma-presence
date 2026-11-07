# Intention : indemnités kilométriques (IK) des admins

Validée le 2026-11-07.

- **Résultat :** chaque compte admin (Elise aujourd'hui) a une ligne à son nom, en dernier dans le tableau du mois. Il n'y saisit que des déplacements, avec les motifs habituels « nom + km » : ni heures +/-, ni absences.
- **Bénéficiaires :** l'admin, pour ses propres IK, et le comptable, qui reçoit l'export une fois par an.
- **Saisie :** chaque admin ne saisit que sur sa propre ligne. Les lignes des autres admins sont visibles en lecture seule. Les déplacements des admins sont tracés dans l'Historique.
- **Exclusions :** les km des admins n'apparaissent ni dans l'export « État préparatoire », ni dans les Statistiques, ni dans le compteur d'heures +/-.
- **Export :** un bouton « Télécharger mes IK » avec un sélecteur d'année (l'année en cours par défaut). Il produit un Excel de l'admin connecté :
  - colonnes Mois | Km | Montant (= km × coefficient), sur 12 lignes (mois sans km à 0) ;
  - une ligne Total km et Total montant ;
  - le nom, l'année et le coefficient rappelés dans le fichier.
- **Paramètre :** un « Coefficient IK » unique en €/km, avec trois décimales (ex. 0,636), réglable dans Paramètres et appliqué à toute l'année exportée.
- **Hors périmètre :**
  - pas d'historique des coefficients ;
  - pas d'export des IK d'un autre admin ;
  - pas de fichier qui regroupe tous les admins ;
  - pas d'heures +/- ni d'absences pour les admins ;
  - pas de faux employés visibles côté employé.
