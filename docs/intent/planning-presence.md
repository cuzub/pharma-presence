# Intention validée — Planning de présence par demi-journée

Validée le 2026-11-24.

## Intention
- **Résultat attendu :** un planning de présence par demi-journée dans le *Tableau du mois* : qui est là le matin et l'après-midi, combien de personnes sont présentes, et combien d'heures chacun fait par semaine.
- **Utilisateurs :**
  - la pharmacienne : saisit les trames (la sienne comprise) et les exceptions ;
  - l'employé : voit son propre planning dans *Mon mois*, en lecture seule.
- **Pourquoi :** organiser l'équipe et vérifier la couverture de l'officine.
- **Critère de réussite :** en ouvrant le mois, la pharmacienne repère d'un coup d'œil une demi-journée en sous-effectif, sans autre outil.

## Données
- **Trame** par employé et pour la pharmacienne :
  - semaine 1 = semaine ISO impaire, semaine 2 = semaine ISO paire ;
  - du lundi au samedi, un horaire matin et un horaire après-midi, éventuellement vides ;
  - une date de début : la nouvelle trame s'applique à partir de cette date, les semaines passées gardent l'ancienne.
- **Saisie d'une trame** *(modifié le 2026-11-26)* : la fenêtre *Planning* (employés et pharmacienne) affiche toujours un champ « Applicable à partir du » ; « Enregistrer » applique directement, sans étape intermédiaire. Si une trame commence déjà à cette date, elle est remplacée ; sinon une nouvelle trame commence à cette date. Dans les deux cas, les trames plus récentes sont supprimées : les nouveaux horaires s'appliquent à tout le planning à venir. Plus de choix « Corriger / Nouveau planning ».
- **Exception** à la journée : elle remplace la trame ce jour-là (événement exceptionnel).
- **Plages fixes :**
  - matin 9h → 12h30 ;
  - pause 12h30 → 13h30 ;
  - après-midi 13h30 → 19h30 ;
  - le samedi, le matin seulement.
- **Couleur :**
  - réglable par employé dans l'écran *Employés* ;
  - bleu cyan fixe (dans le code) pour la pharmacienne.

## Affichage du Tableau du mois
- Chaque jour est découpé en deux cases (matin / après-midi), plus larges. Chaque case est remplie à la couleur de la personne au prorata de sa présence, blanc ailleurs (ex. arrivée à 10h : blanc de 9h à 10h, couleur ensuite).
- Les jours d'absence sont grisés d'une seule couleur, quel que soit le motif. Les jours de fermeture et fériés sont aussi grisés.
- La colonne du dimanche est remplacée par le **total d'heures prévues de la semaine**, absences **non** déduites.
- Une ligne en bas compte les **présents à la fermeture de chaque demi-journée** (horaire prévu jusqu'à 12h30 pour le matin, 19h30 pour l'après-midi), pharmacienne comprise : deux nombres par jour (un le samedi), alignés à droite. Un employé absent ce jour-là n'est pas compté. *(Modifié le 2026-11-25 : remplace le compte par demi-journée.)*
- Un nombre s'affiche **en blanc sur fond rouge** s'il est strictement inférieur au seuil réglé dans *Paramètres* : un seuil pour la semaine (midi et soir), un pour le samedi, sans valeur par défaut (vide = pas d'alerte). Les heures de fermeture restent fixes.
- La saisie des heures +/-, des déplacements et des absences ne change pas.

## Contraintes
- Le planning et les heures +/- restent séparés : le planning est une prévision, aucun écart n'est calculé automatiquement.
- La stack ne change pas (Vue 3, Flask, PostgreSQL).
- L'export comptable ne change pas.

## Hors périmètre
- Absences à la demi-journée (version ultérieure).
- Total mensuel des heures du planning.
- Calcul de paie, écart planning / contrat.
- Génération automatique des heures +/-.
- Saisie ou modification des horaires par les employés.
- Vue du planning d'équipe pour les employés.
- Planning du dimanche.
