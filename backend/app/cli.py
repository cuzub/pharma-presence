"""Commandes d'administration : `flask creer-admin`, `flask reinitialiser-mdp`, `flask demo`."""

import secrets
from datetime import date, timedelta

import click

from app.extensions import db
from app.models import Absence, Contrat, Deplacement, Employe, HeuresEnPlus, MotifAbsence, MotifDeplacement, Utilisateur


def _mot_de_passe_aleatoire():
    return secrets.token_urlsafe(12)


def enregistrer_commandes(app):
    @app.cli.command('creer-admin')
    @click.argument('identifiant')
    def creer_admin(identifiant):
        """Crée le compte de la pharmacienne avec un mot de passe provisoire."""
        identifiant = identifiant.strip().lower()
        if Utilisateur.query.filter_by(identifiant=identifiant).first():
            raise click.ClickException('Cet identifiant existe déjà.')
        mot_de_passe = _mot_de_passe_aleatoire()
        admin = Utilisateur(identifiant=identifiant, role=Utilisateur.ROLE_ADMIN, actif=True)
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
    def demo():
        """Développement uniquement : crée des données FICTIVES (admin/admin-demo-1234)."""
        if app.config.get('ENV_NAME') != 'development':
            raise click.ClickException('Commande réservée au développement (FLASK_ENV=development).')
        if Utilisateur.query.first():
            raise click.ClickException('La base contient déjà des comptes.')

        admin = Utilisateur(identifiant='admin', role=Utilisateur.ROLE_ADMIN)
        admin.definir_mot_de_passe('admin-demo-1234', provisoire=False)
        db.session.add(admin)
        motifs = {m.code: m for m in MotifAbsence.query.all()}
        destinations = [MotifDeplacement(libelle=libelle, km=km, ordre=ordre) for ordre, (libelle, km) in enumerate(
            [('Domitis', 2), ('Orgères', 5), ('LCL', 30)], start=1)]
        db.session.add_all(destinations)
        aujourdhui = date.today()
        debut_mois = aujourdhui.replace(day=1)
        fictifs = [
            ('MARTIN', 'Alice', 151.67), ('DURAND', 'Bruno', 151.67), ('PETIT', 'Chloé', 121.33),
            ('LEROY', 'David', 69.33), ('MOREAU', 'Emma', 151.67),
        ]
        for index, (nom, prenom, heures) in enumerate(fictifs):
            utilisateur = Utilisateur(identifiant=prenom.lower().replace('é', 'e'), role=Utilisateur.ROLE_EMPLOYE)
            utilisateur.definir_mot_de_passe('employe-demo-1234', provisoire=False)
            employe = Employe(nom=nom, prenom=prenom, utilisateur=utilisateur)
            db.session.add_all([utilisateur, employe, Contrat(employe=employe, heures_mensuelles=heures, date_debut=date(2024, 1, 1))])
            db.session.flush()
            if index == 0:
                db.session.add(Absence(employe_id=employe.id, motif=motifs['CP'], date_debut=debut_mois + timedelta(days=9), date_reprise=debut_mois + timedelta(days=16)))
            if index == 1:
                db.session.add(HeuresEnPlus(employe_id=employe.id, jour=debut_mois + timedelta(days=2), minutes=90))
                db.session.add(HeuresEnPlus(employe_id=employe.id, jour=debut_mois + timedelta(days=5), minutes=-30))
                db.session.add(Deplacement(employe_id=employe.id, date=debut_mois + timedelta(days=3), motif_deplacement=destinations[2], motif='LCL', km=30))
                db.session.add(Deplacement(employe_id=employe.id, date=debut_mois + timedelta(days=8), motif='Grossiste (récupération de commande)', km=24))
            if index == 2:
                db.session.add(Absence(employe_id=employe.id, motif=motifs['MAL'], date_debut=debut_mois + timedelta(days=4), date_reprise=debut_mois + timedelta(days=7)))
        db.session.commit()
        click.echo('Données de démonstration créées. Connexion : admin / admin-demo-1234 (employés : alice, bruno… / employe-demo-1234)')
