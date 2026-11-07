"""Commandes d'administration : `flask creer-admin`, `flask reinitialiser-mdp`, `flask demo`."""

import secrets
from datetime import date, timedelta

import click
from sqlalchemy import text

from app.extensions import db
from app.models import (
    Absence, Contrat, Deplacement, Employe, HeuresEnPlus, MotifAbsence, MotifDeplacement, RegularisationHeures, Utilisateur,
)

_TABLES_DEMO = [
    'parametres_ik', 'journal_modifications', 'regularisations_heures', 'heures_en_plus', 'deplacements', 'motifs_deplacement',
    'absences', 'contrats', 'employes', 'jours_fermeture',
]

# Équipe fictive : nom, prénom, contrat (h/mois), tendance des heures +/- (minutes typiques par saisie).
_EQUIPE_DEMO = [
    ('MARTIN', 'Alice', 151.67, 30), ('DURAND', 'Bruno', 151.67, 60), ('PETIT', 'Chloé', 121.33, -15),
    ('LEROY', 'David', 69.33, 15), ('MOREAU', 'Emma', 151.67, 45), ('GARNIER', 'Fanny', 121.33, -30),
]


def _mot_de_passe_aleatoire():
    return secrets.token_urlsafe(12)


def enregistrer_commandes(app):
    @app.cli.command('creer-admin')
    @click.argument('identifiant')
    @click.option('--nom', default=None, help='Nom affiché (ex : Elise), utilisé dans le tableau et l\'export IK.')
    def creer_admin(identifiant, nom):
        """Crée le compte de la pharmacienne avec un mot de passe provisoire."""
        identifiant = identifiant.strip().lower()
        if Utilisateur.query.filter_by(identifiant=identifiant).first():
            raise click.ClickException('Cet identifiant existe déjà.')
        mot_de_passe = _mot_de_passe_aleatoire()
        admin = Utilisateur(identifiant=identifiant, role=Utilisateur.ROLE_ADMIN, actif=True)
        admin.nom_affiche = nom.strip() if nom and nom.strip() else None
        admin.definir_mot_de_passe(mot_de_passe, provisoire=True)
        db.session.add(admin)
        db.session.commit()
        click.echo(f'Compte administrateur « {identifiant} » créé.')
        click.echo(f'Mot de passe provisoire (à changer à la première connexion) : {mot_de_passe}')

    @app.cli.command('reinitialiser-mdp')
    @click.argument('identifiant')
    def reinitialiser_mdp(identifiant):
        """Secours : définit un mot de passe provisoire pour n'importe quel compte (y compris admin)."""
        utilisateur = Utilisateur.query.filter_by(identifiant=identifiant.strip().lower()).first()
        if utilisateur is None:
            raise click.ClickException('Compte introuvable.')
        mot_de_passe = _mot_de_passe_aleatoire()
        utilisateur.definir_mot_de_passe(mot_de_passe, provisoire=True)
        utilisateur.actif = True
        db.session.commit()
        click.echo(f'Mot de passe provisoire pour « {utilisateur.identifiant} » : {mot_de_passe}')

    @app.cli.command('demo')
    @click.option('--reinitialiser', is_flag=True, help='Vide d\'abord toutes les données (comptes, saisies, motifs de déplacement).')
    def demo(reinitialiser):
        """Développement uniquement : crée des données FICTIVES (admin/admin-demo-1234, 6 employés)."""
        if app.config.get('ENV_NAME') != 'development':
            raise click.ClickException('Commande réservée au développement (FLASK_ENV=development).')
        if reinitialiser:
            for table in _TABLES_DEMO:
                db.session.execute(text(f'DELETE FROM {table}'))
            db.session.execute(text('UPDATE motifs_absence SET updated_by_id = NULL'))
            db.session.execute(text('DELETE FROM utilisateurs'))
            db.session.commit()
        if Utilisateur.query.first():
            raise click.ClickException('La base contient déjà des comptes (utilisez --reinitialiser).')
        _creer_demo()
        click.echo('Données de démonstration créées. Connexion : admin / admin-demo-1234 (employés : alice, bruno… / employe-demo-1234)')


def _creer_demo():
    """Deux ans d'historique fictif et reproductible : heures +/-, absences, déplacements, régularisations."""
    import random

    hasard = random.Random(42)
    aujourdhui = date.today()
    debut_historique = date(aujourdhui.year - 1, 1, 1)

    admin = Utilisateur(identifiant='admin', role=Utilisateur.ROLE_ADMIN, nom_affiche='Elise')
    admin.definir_mot_de_passe('admin-demo-1234', provisoire=False)
    db.session.add(admin)
    motifs = {m.code: m for m in MotifAbsence.query.all()}
    destinations = [MotifDeplacement(libelle=libelle, km=km, ordre=ordre) for ordre, (libelle, km) in enumerate(
        [('Domitis', 2), ('Orgères', 5), ('LCL', 30)], start=1)]
    db.session.add_all(destinations)

    for index, (nom, prenom, heures, tendance) in enumerate(_EQUIPE_DEMO):
        utilisateur = Utilisateur(identifiant=prenom.lower().replace('é', 'e'), role=Utilisateur.ROLE_EMPLOYE)
        utilisateur.definir_mot_de_passe('employe-demo-1234', provisoire=False)
        employe = Employe(nom=nom, prenom=prenom, utilisateur=utilisateur)
        db.session.add_all([utilisateur, employe, Contrat(employe=employe, heures_mensuelles=heures, date_debut=date(2024, 1, 1))])
        db.session.flush()

        # Congés d'été (une semaine décalée par employé) et une absence dans le mois en cours pour certains.
        absences = []
        for annee in (aujourdhui.year - 1, aujourdhui.year):
            debut_cp = date(annee, 7, 6) + timedelta(weeks=index)
            absences.append((motifs['CP'], debut_cp, debut_cp + timedelta(days=7)))
        debut_mois = aujourdhui.replace(day=1)
        if index == 0:
            absences.append((motifs['CP'], debut_mois + timedelta(days=9), debut_mois + timedelta(days=16)))
        if index == 2:
            absences.append((motifs['MAL'], debut_mois + timedelta(days=4), debut_mois + timedelta(days=7)))
        if index == 4:
            absences.append((motifs['RECUP'], debut_mois + timedelta(days=18), debut_mois + timedelta(days=20)))
        for motif, debut, reprise in absences:
            db.session.add(Absence(employe_id=employe.id, motif=motif, date_debut=debut, date_reprise=reprise))

        def absent(jour):
            return any(debut <= jour < reprise for _, debut, reprise in absences)

        jour = debut_historique
        while jour <= aujourdhui:
            if jour.weekday() != 6 and not absent(jour):
                if hasard.random() < 0.2:
                    minutes = tendance + hasard.choice([-60, -45, -30, -15, 0, 15, 30, 45, 60])
                    minutes = max(-240, min(240, minutes)) // 15 * 15
                    if minutes:
                        db.session.add(HeuresEnPlus(employe_id=employe.id, jour=jour, minutes=minutes))
                if index in (1, 3) and hasard.random() < 0.08:
                    destination = hasard.choice(destinations)
                    db.session.add(Deplacement(
                        employe_id=employe.id, date=jour, motif_deplacement=destination, motif=destination.libelle, km=destination.km,
                    ))
            jour += timedelta(days=1)

    employes = {e.prenom: e for e in Employe.query.all()}
    fin_mois_precedent = aujourdhui.replace(day=1) - timedelta(days=1)
    db.session.add_all([
        RegularisationHeures(employe_id=employes['Bruno'].id, jour=fin_mois_precedent, minutes=-600, commentaire='Heures payées sur la paie'),
        RegularisationHeures(employe_id=employes['Fanny'].id, jour=debut_historique, minutes=300, commentaire="Solde de départ (avant l'outil)"),
        RegularisationHeures(employe_id=employes['Emma'].id, jour=aujourdhui.replace(day=1) + timedelta(days=18), minutes=-420, commentaire='Récupération'),
    ])

    # Trajets de l'admin (IK), une dizaine sur deux ans.
    db.session.flush()
    jour = debut_historique
    while jour <= aujourdhui:
        if jour.weekday() != 6 and hasard.random() < 0.015:
            destination = hasard.choice(destinations)
            db.session.add(Deplacement(
                utilisateur_id=admin.id, date=jour, motif=destination.libelle, km=destination.km,
            ))
        jour += timedelta(days=1)
    db.session.commit()
