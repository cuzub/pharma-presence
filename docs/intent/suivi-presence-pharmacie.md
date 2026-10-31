# Intention validée — Suivi de présence de l'équipe (pharmacie)

Validée le 2026-10-30. Version 2 : révisée après analyse du fichier « etats péparatoires 2025.xlsx ».

## Principe directeur
L'outil **enregistre les faits, le comptable interprète**. Aucun calcul de paie.

## Intention
- **Résultat attendu :** une application web (ordinateur) qui remplace l'« état préparatoire » Excel envoyé chaque mois au comptable.
- **Utilisateurs :**
  - la pharmacienne : accès complet (voir, modifier, valider, exporter) ;
  - ses 10 employés : consultation de leurs propres données et déclaration de leurs déplacements.
- **Pourquoi maintenant :** les erreurs et les oublis du fichier Excel (par exemple une période notée « 6CP » en février alors qu'elle ne compte qu'un jour ouvrable dans ce mois).
- **Critère de réussite :** chaque mois, l'export part au comptable sans aucune retouche. Avant l'export, l'outil montre un calendrier du mois et signale les points en attente (déplacements non validés, etc.).
- **Contraintes :**
  - la pharmacienne développe et maintient l'outil seule, donc la stack doit rester simple (React était une préférence ; décision finale : Vue 3 + Flask + PostgreSQL, en reprenant l'architecture du projet Pedalog, hébergé sur un Raspberry Pi dédié) ;
  - pas de contrainte de budget ;
  - les données sont sensibles (RGPD : motif « maladie ») : connexion sécurisée et chaque employé ne voit que ses propres données.

## Données
- **Employé :** nom, prénom, contrat en heures par mois (par exemple 151,67 / 121,33 / 69,33).
- **Présence :** implicite. Un employé est présent par défaut ; on ne saisit que les exceptions.
- **Absence :** saisie par période (premier jour d'absence, jour de reprise) avec un motif (CP, maladie, récupération, congé maternité, ...). La date de fin peut rester ouverte, et une période peut couvrir plusieurs mois. L'outil remplit les jours du calendrier, mais **ne compte pas** les jours.
- **Heures en plus :** un seul chiffre par employé et par jour, saisi par la pharmacienne, sans classement compl/suppl.
- **Déplacement :** date, motif, km. Déclaré par l'employé puis validé par la pharmacienne (la pharmacienne peut aussi en saisir ou en modifier). Voir « Motifs de déplacement » ci-dessous.

## Motifs de déplacement (validé le 2026-10-31)
- **Résultat :** saisir un déplacement en 2 clics : clic sur la date du calendrier → choix du motif → km remplis automatiquement → enregistrer.
- **Motifs (admin) :** dans *Paramètres*, la pharmacienne crée / modifie / désactive des motifs « nom + km » (ex. Domitis 2 km, Orgères 5 km, LCL 30 km). Le km saisi est celui qui est compté. Un motif désactivé n'est plus proposé ; l'historique est conservé.
- **« Autre » :** toujours proposé ; km libres + précision obligatoire (ex. « Pharmacie de Chartres »).
- **Calendrier unique :** les déplacements apparaissent dans le calendrier du mois, avec un crayon pour les modifier (comme Pedalog).
  - Employé : clic sur une date = saisie d'un déplacement (plusieurs par jour possibles) ; il modifie / supprime les siens tant qu'ils ne sont pas validés.
  - Admin : clic sur une date = fenêtre heures / absence + section « Déplacements du jour » (ajouter, modifier, supprimer).
- **Historique figé :** chaque déplacement garde les km et le libellé du moment de sa saisie ; changer la distance d'un motif ne touche que les nouveaux déplacements.
- **Supprimé :** champs Départ / Arrivée et page séparée « Mes déplacements ».
- **Hors périmètre :** barème kilométrique, calcul d'itinéraire, carte. L'export garde sa structure (colonnes Départ / Arrivée remplacées par le motif).
- **Reprise :** les déplacements existants deviennent des « Autre » (motif + trajet conservés dans la précision).

## Export mensuel (CSV + Excel)
- **Onglet Récapitulatif :** une ligne par employé avec nom, prénom, contrat (h/mois), total des heures en plus, périodes d'absence (jour d'absence, jour de reprise, motif) et total des km validés.
- **Onglet Détail :** les heures en plus jour par jour, pour chaque employé.

## Hors périmètre
- Tout calcul de paie : classement des heures (complémentaires, supplémentaires 25 % / 50 %), nombre de jours de CP, montant des indemnités kilométriques.
- Primes et acomptes (pour le moment).
- Saisie des jours de présence.
- Demandes de congés et saisie des heures par les employés.
- Version mobile.
- Planning prévisionnel.
