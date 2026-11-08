# Guide d'utilisation

## Pour la pharmacienne

### Chaque jour (ou quand c'est nécessaire)

Par défaut, chaque employé est **présent**. Vous ne saisissez que les exceptions.

- **Heures en plus / en moins** : *Tableau* → clic sur la case de l'employé et du jour → saisissez
  des **minutes**, par tranche de 5 : `15` = 15 min en plus, `-30` = 30 min en moins, `90` = 1h30
  en plus (12 h maximum par jour) → *Enregistrer*. Pour effacer, cliquez sur la gomme (elle vide le
  champ) puis *Enregistrer*.
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

Menu **Employés** : la colonne *Solde H +/-* donne le compteur de chacun à ce jour. Le bouton
**Heures +/-** de la ligne ouvre une fenêtre dédiée :

1. En haut, le **solde à ce jour**.
2. **Motif** (raccourci, facultatif) : *Heures payées* ou *Récupération* (retirent des heures),
   *Solde de départ* (ajoute), *Correction*. Le sens et le commentaire sont préremplis.
3. **Opération** : *Ajouter au compteur* ou *Retirer du compteur*.
4. **Durée** (heures et minutes), **date** (aujourd'hui par défaut) et commentaire facultatif.
5. L'aperçu « Solde : avant → après » se met à jour ; cliquez sur *Enregistrer*.

Dessous, l'**historique des régularisations** : le crayon recharge une opération dans le formulaire
pour la corriger, la poubelle la supprime (tout est tracé dans l'*Historique*).

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

### Vos indemnités kilométriques (IK)

Vos déplacements professionnels se saisissent sur **votre propre ligne**, en bas du *Tableau* du
mois. Cette ligne ne sert qu'à vos IK : elle n'apparaît ni dans l'État préparatoire, ni dans les
récapitulatifs des employés.

- **Saisie** : cliquez sur une case de votre ligne, comme pour un employé, pour ajouter un
  déplacement (motif, km). Les lignes des autres admins sont en lecture seule.
- **Coefficient et nom** : réglez-les dans **Paramètres** → *Indemnités kilométriques*. Le nom
  affiché est celui qui apparaît sur votre ligne et dans l'export.
- **Export annuel** : menu **Export**, carte *Indemnités kilométriques* ; choisissez l'année et
  téléchargez le fichier Excel (km et montant par mois, totaux).

### En fin de mois : l'export pour le comptable

Menu **Export** :
1. Vérifiez l'aperçu, ou le *Tableau* d'un coup d'œil.
2. Téléchargez l'**État préparatoire Excel** et envoyez-le au comptable, ou cliquez sur
   **Envoyer par mail** : votre messagerie s'ouvre avec un nouveau mail pré-rempli (destinataire,
   titre, texte) et l'Excel est téléchargé. Joignez le fichier au mail (glisser-déposer), relisez
   et envoyez.

Le destinataire, le titre et le texte du mail se configurent dans **Paramètres** → *Envoi de
l'export par mail*. `{mois}` y est remplacé par le mois exporté (ex : Octobre 2026).

Le fichier Excel contient 3 onglets : *Récapitulatif* (une ligne par employé : contrat, périodes
d'absence, km), *Absences* et *Déplacements* (justificatif des kilomètres). Les heures +/- et les
entrées / sorties ne figurent pas dans l'export (elles restent visibles dans le *Tableau* du mois). Les
déplacements des admins (indemnités kilométriques) n'y figurent pas non plus : ils ont leur propre export annuel.

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
