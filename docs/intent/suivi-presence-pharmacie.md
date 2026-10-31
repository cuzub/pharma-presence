# Intention validée — Suivi de présence de l'équipe (pharmacie)

Validée le 2026-10-30. Version 2 : révisée après analyse du fichier « etats péparatoires 2025.xlsx ».

## Principe directeur
L'outil **enregistre les faits, le comptable interprète**. Aucun calcul de paie.

## Intention
- **Résultat attendu :** une application web (ordinateur) qui remplace l'« état préparatoire » Excel envoyé chaque mois au comptable.
- **Utilisateurs :**
  - la pharmacienne : accès complet (voir, modifier, exporter, consulter l'historique) ;
  - ses 10 employés : consultation de leurs propres données et déclaration de leurs déplacements.
- **Pourquoi maintenant :** les erreurs et les oublis du fichier Excel (par exemple une période notée « 6CP » en février alors qu'elle ne compte qu'un jour ouvrable dans ce mois).
- **Critère de réussite :** chaque mois, l'export part au comptable sans aucune retouche. Avant l'export, l'outil montre un calendrier du mois et signale les incohérences à vérifier.
- **Contraintes :**
  - la pharmacienne développe et maintient l'outil seule, donc la stack doit rester simple (React était une préférence ; décision finale : Vue 3 + Flask + PostgreSQL, en reprenant l'architecture du projet Pedalog, hébergé sur un Raspberry Pi dédié) ;
  - pas de contrainte de budget ;
  - les données sont sensibles (RGPD : motif « maladie ») : connexion sécurisée et chaque employé ne voit que ses propres données.

## Données
- **Employé :** nom, prénom, contrat en heures par mois (par exemple 151,67 / 121,33 / 69,33).
- **Présence :** implicite. Un employé est présent par défaut ; on ne saisit que les exceptions.
- **Absence :** saisie par période (premier jour d'absence, jour de reprise) avec un motif (CP, maladie, récupération, congé maternité, ...). La date de fin peut rester ouverte, et une période peut couvrir plusieurs mois. L'outil remplit les jours du calendrier, mais **ne compte pas** les jours.
- **Heures en plus / en moins :** un nombre de minutes signé par employé et par jour (par 5, ±12 h max ; ex. `15`, `-30`), saisi par la pharmacienne, sans classement compl/suppl. Affichage « +1h30 » / « -30min » ; export en minutes, total net.
- **Déplacement :** date, motif, km. Purement déclaratif (pas de validation). Voir « Motifs de déplacement » et « Version 1.2.0 » ci-dessous.

## Motifs de déplacement (validé le 2026-10-31)
- **Résultat :** saisir un déplacement en 2 clics : clic sur la date du calendrier → choix du motif → km remplis automatiquement → enregistrer.
- **Motifs (admin) :** dans *Paramètres*, la pharmacienne crée / modifie / désactive des motifs « nom + km » (ex. Domitis 2 km, Orgères 5 km, LCL 30 km). Le km saisi est celui qui est compté. Un motif désactivé n'est plus proposé ; l'historique est conservé.
- **« Autre » :** toujours proposé ; km libres + précision obligatoire (ex. « Pharmacie de Chartres »).
- **Calendrier unique :** les déplacements apparaissent dans le calendrier du mois, avec un crayon pour les modifier (comme Pedalog).
  - Employé : clic sur une date = saisie d'un déplacement (plusieurs par jour possibles) ; il modifie / supprime les siens (fenêtre : voir version 1.2.0).
  - Admin : clic sur une date = fenêtre heures / absence + section « Déplacements du jour » (ajouter, modifier, supprimer).
- **Historique figé :** chaque déplacement garde les km et le libellé du moment de sa saisie ; changer la distance d'un motif ne touche que les nouveaux déplacements.
- **Supprimé :** champs Départ / Arrivée et page séparée « Mes déplacements ».
- **Hors périmètre :** barème kilométrique, calcul d'itinéraire, carte. L'export garde sa structure (colonnes Départ / Arrivée remplacées par le motif).
- **Reprise :** les déplacements existants deviennent des « Autre » (motif + trajet conservés dans la précision).

## Version 1.2.0 (validée le 2026-10-31)
- **Déplacements déclaratifs :** plus de statut, de validation ni de refus ; tous comptent (y compris les anciens en attente / refusés). Aucun blocage de l'export.
  - Employé : crée / modifie / supprime les siens pour le mois en cours, et le mois précédent jusqu'au 5 inclus (règle appliquée par le serveur, heure de Paris).
  - Pharmacienne : tout, sans limite.
- **Heures +/- en minutes :** voir « Données ». Conversion des saisies existantes (1,5 h → 90 min).
- **Historique des modifications :** créations / modifications / suppressions de déplacements, heures +/- et absences, avec date et heure, auteur, employé concerné et avant → après. Filtres : employé, mois, auteur, type. Immuable, conservé indéfiniment, réservé à la pharmacienne ; démarre à la mise en ligne (pas de rétroactif).
- **Hors périmètre :** historique des fiches employés, saisie des heures par les employés.

## Version 1.3.0 — Statistiques (validée le 2026-10-31)
- **Page « Statistiques » :** réservée à la pharmacienne (menu « Statistiques », après Historique).
- **Année :** navigation ‹ › ; l'année en cours par défaut, les années passées sont consultables (lien « Cette année »). L'année est conservée dans l'URL (`?annee=AAAA`).
- **Graphique :** barres empilées par mois, une couleur par employé ; heures en plus au-dessus de l'axe, en moins en dessous. Clic sur un nom de la légende : masque ou affiche l'employé.
- **Tableau :** par employé et par mois, le net (plus moins moins), avec le détail plus / moins au survol ; colonne Total annuel et ligne Équipe.
- **Employés inclus :** ceux qui ont une saisie ou un contrat sur l'année, y compris les employés partis (mention « parti »).
- **Hors périmètre :** export des statistiques, statistiques des déplacements et des absences, vue employé, ratio par rapport au contrat.

## Version 1.4.0 (validée le 2026-10-31)
- **Statistiques en net :** un jeu de données par employé (net mensuel en heures, barres empilées : le positif monte, le négatif descend). Clic sur un employé (légende ou ligne du tableau) pour l'isoler ; un bandeau « Vue : Prénom NOM ✕ » permet de revenir à l'équipe. L'isolement est conservé au changement d'année si l'employé est toujours présent.
- **Tableau du mois :** colonnes Employé (à gauche), H +/- et Km (à droite) figées lors du défilement horizontal. Chaque case affiche les km du jour sous les minutes ; l'info-bulle détaille les déplacements.
- **Blocage pendant les absences :** un motif a une option « Bloque heures et déplacements » (migration 0004 : vrai par défaut, faux pour Formation et Autre).
  - Un jour couvert par une absence bloquante refuse les heures non nulles et la création ou la modification de déplacement, quel que soit le rôle. L'effacement et la suppression restent permis.
  - Créer ou étendre une absence bloquante qui touche des saisies existantes renvoie la liste des conflits ; la suppression de ces saisies exige une confirmation explicite, et chaque suppression est journalisée.
  - Une absence en cours couvre tous les jours à partir de son début.
- **Hors périmètre :** saisie des heures par les employés, calcul de paie.

## Export mensuel (CSV + Excel)
- **Onglet Récapitulatif :** une ligne par employé avec nom, prénom, contrat (h/mois), total net des heures +/- (en minutes), périodes d'absence (jour d'absence, jour de reprise, motif) et total des km.
- **Onglet Détail :** les heures +/- jour par jour (en minutes), pour chaque employé.

## Hors périmètre
- Tout calcul de paie : classement des heures (complémentaires, supplémentaires 25 % / 50 %), nombre de jours de CP, montant des indemnités kilométriques.
- Primes et acomptes (pour le moment).
- Saisie des jours de présence.
- Demandes de congés et saisie des heures par les employés.
- Version mobile.
- Planning prévisionnel.
