# Guide d'utilisation

## Pour la pharmacienne

### Chaque jour (ou quand c'est nécessaire)

Par défaut, chaque employé est **présent**. Vous ne saisissez que les exceptions.

- **Heures en plus** : *Tableau du mois* → clic sur la case de l'employé et du jour → saisissez
  le nombre d'heures (ex. `1,5`) → *Enregistrer*. Pour effacer, mettez `0` ou cliquez sur la gomme.
- **Absence** : clic sur le premier jour d'absence → *Déclarer une absence à partir de ce jour* →
  motif et **jour de reprise** (le premier jour où l'employé revient). Laissez le jour de reprise
  vide s'il n'est pas connu (congé maternité, arrêt maladie sans date de fin) : l'absence reste
  « en cours » jusqu'à ce que vous le renseigniez.
- **Déplacements** : le badge orange du menu *Déplacements* indique les déclarations à valider.
  Pour en saisir un vous-même : *Calendrier* (ou *Tableau du mois*) → clic sur le jour →
  *Ajouter un déplacement*. Il est validé directement. Pour le corriger : le crayon.

### Motifs de déplacement

Menu **Paramètres** → *Motifs de déplacement* : créez vos destinations habituelles avec leur
distance (ex. Domitis 2 km, Orgères 5 km, LCL 30 km). Lors de la saisie d'un déplacement, il suffit
de choisir le motif : les kilomètres sont remplis automatiquement. « Autre » est toujours proposé
pour une destination ponctuelle (distance et précision libres).

Changer la distance d'un motif ne modifie **pas** les déplacements déjà saisis (ils gardent la
distance du moment). Un motif qui ne sert plus se **désactive** (case *Actif*) : il n'est plus
proposé, mais reste visible sur les anciens déplacements.

### Arrivée, changement de contrat, départ

Menu **Employés** :
- *Nouvel employé* : nom, prénom, date d'entrée, contrat (heures/mois). L'identifiant et un mot de
  passe provisoire sont proposés : transmettez-les à l'employé, il choisira son propre mot de passe à
  la première connexion.
- *Gérer* → **Avenant** : nouveau nombre d'heures à partir d'une date (l'ancien contrat est clôturé
  la veille).
- *Gérer* → **Départ** : dernier jour sous contrat. Le compte est désactivé immédiatement, les données
  sont conservées et l'employé apparaît encore dans les exports des mois où il était présent.
- *Gérer* → **Retour de l'employé** : pour un ancien employé qui revient (ex. étudiant l'été).
- *Gérer* → **Mot de passe oublié** : génère un nouveau mot de passe provisoire.

### En fin de mois : l'export pour le comptable

Menu **Export comptable** :
1. Lisez les **contrôles** : les points rouges bloquent l'export (ex. déplacement non validé), les
   points orange sont des incohérences à vérifier (ex. heures en plus pendant une absence).
2. Vérifiez l'aperçu, ou le *Tableau du mois* d'un coup d'œil.
3. Téléchargez l'**État préparatoire Excel** (ou les CSV) et envoyez-le au comptable.

Le fichier Excel contient 4 onglets : *Récapitulatif* (une ligne par employé), *Absences*,
*Heures en plus* (détail jour par jour) et *Déplacements* (justificatif des kilomètres).

## Pour les employés

- **Mon mois** : vos absences et heures en plus, saisies par la pharmacienne. Une erreur ?
  Signalez-la-lui.
- **Déplacements** : dans *Mon mois*, cliquez sur la date du déplacement → choisissez le motif
  (les kilomètres se remplissent tout seuls) → *Enregistrer*. Si la destination n'est pas dans la
  liste, choisissez « Autre » et saisissez la précision et les kilomètres. Plusieurs déplacements
  par jour sont possibles.
  Pour corriger ou supprimer un déplacement, cliquez sur le **crayon** (possible tant qu'il n'est
  pas validé). Couleurs : orange = en attente, vert = validé, rouge = refusé (le motif du refus
  s'affiche au survol et dans la fenêtre : corrigez-le, il repassera en attente de validation).
- Pour changer votre mot de passe : cliquez sur votre nom en haut à droite.
