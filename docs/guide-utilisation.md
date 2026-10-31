# Guide d'utilisation

## Pour la pharmacienne

### Chaque jour (ou quand c'est nécessaire)

Par défaut, chaque employé est **présent**. Vous ne saisissez que les exceptions.

- **Heures en plus / en moins** : *Tableau* → clic sur la case de l'employé et du jour → saisissez
  des **minutes**, par tranche de 5 : `15` = 15 min en plus, `-30` = 30 min en moins, `90` = 1h30
  en plus (12 h maximum par jour) → *Enregistrer*. Pour effacer, mettez `0` ou cliquez sur la gomme.
  À l'écran : « +1h30 » en vert, « -30min » en orange ; le net du mois est calculé (les minutes en
  moins compensent les minutes en plus).
- **Tableau du mois** : sous les minutes de chaque case, le nombre de **km du jour** (somme des
  déplacements). Le nom de l'employé reste visible à gauche, et les colonnes **H +/-** et **Km**
  restent visibles à droite : faites défiler horizontalement pour lire les jours du mois.
  La colonne **H +/-** donne le **solde cumulé** de l'employé à la fin du mois affiché : toutes
  ses heures en plus / en moins depuis le début, régularisations comprises (sans remise à zéro).
  Survolez-la pour voir le net du mois seul.
- **Absence** : clic sur le premier jour d'absence → *Déclarer une absence à partir de ce jour* →
  motif et **jour de reprise** (le premier jour où l'employé revient). Laissez le jour de reprise
  vide s'il n'est pas connu (congé maternité, arrêt maladie sans date de fin) : l'absence reste
  « en cours » jusqu'à ce que vous le renseigniez.
- **Absence bloquante** : pour un motif qui bloque la saisie (par défaut : congés payés, maladie,
  récupération, etc. ; réglable dans *Paramètres*, colonne « Bloque heures et déplacements »), les
  jours de l'absence ne peuvent plus recevoir d'heures +/- ni de déplacement. Si des heures ou des
  déplacements existent déjà sur la période, l'application affiche la liste (« 10/03 : +30min »,
  « 12/03 : Domitis 2 km ») et vous propose de les **supprimer et d'enregistrer l'absence** ; rien
  n'est supprimé sans votre confirmation, et les suppressions figurent dans l'*Historique*. Les
  motifs *Formation* et *Autre* ne bloquent pas la saisie.
- **Déplacements** : ils sont **déclaratifs** (pas de validation) et comptent tous. Le menu
  *Tableau* du mois : clic sur la case du jour → *Ajouter un déplacement*. Dans la même fenêtre,
  le crayon corrige un déplacement et la poubelle le supprime. Vous pouvez modifier n'importe quel
  déplacement, quel que soit le mois. Les km du jour s'affichent sous les minutes, et le total
  des km par employé figure dans la colonne *Km*.

### Régulariser les heures +/- (crédit ou débit)

Menu **Employés** → *Gérer* → section **Heures +/- : régularisations**. Choisissez *Créditer (+)* ou
*Débiter (−)*, la durée (heures et minutes), la date (aujourd'hui par défaut) et, si vous le
souhaitez, un commentaire → *Ajouter*. Exemples : « Heures payées sur la paie d'octobre » (débit),
« Récupération du 15/11 » (débit), « Solde au démarrage de l'outil » (crédit ou débit), correction
d'une erreur. Le solde à ce jour s'affiche en haut de la section ; le crayon modifie une
régularisation et la poubelle la supprime (tout est tracé dans l'*Historique*).

Une régularisation apparaît en **violet** à sa date dans le *Tableau du mois* et dans le calendrier
de l'employé (commentaire au survol), et compte dans le solde (colonne *H +/-*) et dans les
*Statistiques*. Elle n'est liée à aucune absence : quand un employé prend une récupération, saisissez
l'absence *et*, à part, le débit correspondant. Elle ne figure pas dans l'export pour le comptable.

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
plus / en moins, d'une régularisation ou d'une absence est enregistrée avec la date et l'heure, **qui** l'a faite (vous ou
l'employé), l'employé concerné et le détail **avant → après**. Filtrez par employé, mois, auteur ou
type. Cet historique ne peut être ni modifié ni effacé (il commence à la version 1.2.0).

### Statistiques

Menu **Statistiques** (réservé à la pharmacienne) : le cumul des heures en plus / en moins de
l'année, par employé et par mois, régularisations comprises (un crédit compte « en plus », un débit
« en moins »). Par défaut, c'est l'année en cours ; les flèches ‹ › passent à
l'année précédente ou suivante, et le bouton calendrier à leur gauche revient à l'année en cours
(de même, dans le *Tableau* et l'*Export*, il revient au mois en cours).

- **Le graphique** montre, pour chaque mois, une barre par employé, côte à côte : le net du mois,
  au-dessus de l'axe s'il est en plus, en dessous s'il est en moins. Chaque employé a sa couleur.
  Survolez un mois pour voir le détail (« en plus / en moins ») de chacun. Cliquez sur un nom dans
  la légende pour n'afficher que cet employé.
- **Le tableau** donne, pour chaque employé et chaque mois, le **net** (plus moins moins). Survolez
  une case pour voir séparément le plus et le moins. La colonne **Total** donne le net de l'année,
  et la ligne **Équipe** le total de tous les employés.
- **Isoler un employé** : cliquez sur son nom dans la légende ou sur sa ligne du tableau. Le
  graphique et le tableau ne montrent alors que cet employé (ligne surlignée, ligne Équipe conservée).
  Un nouveau clic sur la même ligne (ou dans la légende) rétablit toute l'équipe.
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

Le fichier Excel contient 3 onglets : *Récapitulatif* (une ligne par employé : contrat, périodes
d'absence, km), *Absences* et *Déplacements* (justificatif des kilomètres). Le CSV récapitulatif
reprend les mêmes colonnes. Les heures +/- et les entrées / sorties ne figurent pas dans l'export
(elles restent visibles dans le *Tableau* du mois).

## Pour les employés

- **Mon mois** : vos absences sont saisies par la pharmacienne ; une erreur ? Signalez-la-lui.
  Les **régularisations** (heures payées, récupérations…) qu'elle enregistre apparaissent en violet
  à leur date. Le résumé donne le net du mois et votre **solde cumulé** d'heures +/-.
- **Heures en plus / en moins** : dans *Mon mois*, cliquez sur la date → saisissez les minutes
  (`15`, `-30`) → *Enregistrer*. Mêmes règles de date que pour les déplacements ci-dessous.
- **Déplacements** : dans *Mon mois*, cliquez sur la date du déplacement → *Ajouter un déplacement* → choisissez le motif
  (les kilomètres se remplissent tout seuls) → *Enregistrer*. Si la destination n'est pas dans la
  liste, choisissez « Autre » et saisissez la précision et les kilomètres. Plusieurs déplacements
  par jour sont possibles.
  Pour corriger ou supprimer un déplacement, cliquez sur le **crayon**.
  Vous pouvez saisir, corriger ou supprimer vos déplacements du **mois en cours**, et ceux du
  **mois précédent jusqu'au 5 inclus**. Après, le mois est clôturé : pour un oubli, adressez-vous à
  la pharmacienne.
- Pour changer votre mot de passe : cliquez sur votre nom en haut à droite.
