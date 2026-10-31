# Guide d'utilisation

## Pour la pharmacienne

### Chaque jour (ou quand c'est nécessaire)

Par défaut, chaque employé est **présent**. Vous ne saisissez que les exceptions.

- **Heures en plus / en moins** : *Tableau* → clic sur la case de l'employé et du jour → saisissez
  des **minutes**, par tranche de 5 : `15` = 15 min en plus, `-30` = 30 min en moins, `90` = 1h30
  en plus (12 h maximum par jour) → *Enregistrer*. Pour effacer, mettez `0` ou cliquez sur la gomme.
  À l'écran : « +1h30 » en vert, « -30min » en orange ; le total du mois est net (les minutes en
  moins compensent les minutes en plus).
- **Absence** : clic sur le premier jour d'absence → *Déclarer une absence à partir de ce jour* →
  motif et **jour de reprise** (le premier jour où l'employé revient). Laissez le jour de reprise
  vide s'il n'est pas connu (congé maternité, arrêt maladie sans date de fin) : l'absence reste
  « en cours » jusqu'à ce que vous le renseigniez.
- **Déplacements** : ils sont **déclaratifs** (pas de validation) et comptent tous. Le menu
  *Déplacements* les liste par mois, avec le crayon pour corriger et la poubelle pour supprimer.
  Pour en saisir un vous-même : *Calendrier* (ou *Tableau*) → clic sur le jour →
  *Ajouter un déplacement*. Vous pouvez modifier n'importe quel déplacement, quel que soit le mois.

### Motifs de déplacement

Menu **Paramètres** → *Motifs de déplacement* : créez vos destinations habituelles avec leur
distance (ex. Domitis 2 km, Orgères 5 km, LCL 30 km). Lors de la saisie d'un déplacement, il suffit
de choisir le motif : les kilomètres sont remplis automatiquement. « Autre » est toujours proposé
pour une destination ponctuelle (distance et précision libres).

Changer la distance d'un motif ne modifie **pas** les déplacements déjà saisis (ils gardent la
distance du moment). Un motif qui ne sert plus se **désactive** (case *Actif*) : il n'est plus
proposé, mais reste visible sur les anciens déplacements.

### Historique des modifications

Menu **Historique** : chaque création, modification ou suppression d'un déplacement, d'heures en
plus / en moins ou d'une absence est enregistrée avec la date et l'heure, **qui** l'a faite (vous ou
l'employé), l'employé concerné et le détail **avant → après**. Filtrez par employé, mois, auteur ou
type. Cet historique ne peut être ni modifié ni effacé (il commence à la version 1.2.0).

### Statistiques

Menu **Statistiques** (réservé à la pharmacienne) : le cumul des heures en plus / en moins de
l'année, par employé et par mois. Par défaut, c'est l'année en cours ; les flèches ‹ › passent à
l'année précédente ou suivante, et « Cette année » revient à l'année en cours.

- **Le graphique** empile, pour chaque mois, les heures en plus (au-dessus de l'axe) et en moins
  (en dessous). Chaque employé a sa couleur. Survolez une barre pour voir le détail du mois
  (« en plus / en moins »). Cliquez sur un nom dans la légende pour masquer ou afficher cet employé.
- **Le tableau** donne, pour chaque employé et chaque mois, le **net** (plus moins moins). Survolez
  une case pour voir séparément le plus et le moins. La colonne **Total** donne le net de l'année,
  et la ligne **Équipe** le total de tous les employés.
- Les employés partis dans l'année restent affichés, avec la mention « parti ».

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

Menu **Export** :
1. Lisez les **contrôles** : les points orange sont des incohérences à vérifier (ex. heures en plus
   pendant une absence).
2. Vérifiez l'aperçu, ou le *Tableau* d'un coup d'œil.
3. Téléchargez l'**État préparatoire Excel** (ou les CSV) et envoyez-le au comptable.

Le fichier Excel contient 4 onglets : *Récapitulatif* (une ligne par employé), *Absences*,
*Heures +- (min)* (détail jour par jour, en minutes, avec le total net) et *Déplacements*
(justificatif des kilomètres). Dans le récapitulatif, la colonne *Heures +/- (min)* donne le total
net du mois en minutes (ex. `60`, `-45`).

## Pour les employés

- **Mon mois** : vos absences et heures en plus / en moins, saisies par la pharmacienne. Une
  erreur ? Signalez-la-lui.
- **Déplacements** : dans *Mon mois*, cliquez sur la date du déplacement → choisissez le motif
  (les kilomètres se remplissent tout seuls) → *Enregistrer*. Si la destination n'est pas dans la
  liste, choisissez « Autre » et saisissez la précision et les kilomètres. Plusieurs déplacements
  par jour sont possibles.
  Pour corriger ou supprimer un déplacement, cliquez sur le **crayon**.
  Vous pouvez saisir, corriger ou supprimer vos déplacements du **mois en cours**, et ceux du
  **mois précédent jusqu'au 5 inclus**. Après, le mois est clôturé : pour un oubli, adressez-vous à
  la pharmacienne.
- Pour changer votre mot de passe : cliquez sur votre nom en haut à droite.
