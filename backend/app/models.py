from datetime import datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


def _maintenant():
    return datetime.now(timezone.utc)


def _iso(value):
    return value.isoformat() if value else None


class Horodatage:
    """Colonnes de traçabilité : qui a modifié quoi, et quand."""

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_maintenant)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_maintenant, onupdate=_maintenant)
    updated_by_id = db.Column(db.Integer, db.ForeignKey('utilisateurs.id', ondelete='SET NULL'), nullable=True)


class Utilisateur(Horodatage, db.Model):
    __tablename__ = 'utilisateurs'

    ROLE_ADMIN = 'admin'
    ROLE_EMPLOYE = 'employe'

    id = db.Column(db.Integer, primary_key=True)
    identifiant = db.Column(db.String(80), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(10), nullable=False, default=ROLE_EMPLOYE)
    actif = db.Column(db.Boolean, nullable=False, default=True)
    doit_changer_mdp = db.Column(db.Boolean, nullable=False, default=True)
    # Incrémentée à chaque changement de mot de passe / désactivation : invalide les sessions ouvertes.
    version_session = db.Column(db.Integer, nullable=False, default=1)
    derniere_connexion = db.Column(db.DateTime(timezone=True), nullable=True)

    employe = db.relationship(
        'Employe', back_populates='utilisateur', uselist=False, foreign_keys='Employe.utilisateur_id'
    )

    __table_args__ = (
        db.CheckConstraint("role IN ('admin', 'employe')", name='ck_utilisateurs_role'),
    )

    @property
    def est_admin(self):
        return self.role == self.ROLE_ADMIN

    def definir_mot_de_passe(self, mot_de_passe, provisoire):
        self.password_hash = generate_password_hash(mot_de_passe)
        self.doit_changer_mdp = provisoire
        self.version_session = (self.version_session or 0) + 1

    def verifier_mot_de_passe(self, mot_de_passe):
        return check_password_hash(self.password_hash, mot_de_passe)

    def to_dict(self):
        return {
            'id': self.id,
            'identifiant': self.identifiant,
            'role': self.role,
            'actif': self.actif,
            'doit_changer_mdp': self.doit_changer_mdp,
            'employe_id': self.employe.id if self.employe else None,
            'nom': self.employe.nom if self.employe else None,
            'prenom': self.employe.prenom if self.employe else None,
        }


class Employe(Horodatage, db.Model):
    __tablename__ = 'employes'

    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateurs.id'), nullable=True, unique=True)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)

    utilisateur = db.relationship('Utilisateur', back_populates='employe', foreign_keys=[utilisateur_id])
    contrats = db.relationship(
        'Contrat', back_populates='employe', order_by='Contrat.date_debut', cascade='all, delete-orphan'
    )

    def contrats_sur_periode(self, debut, fin):
        return [c for c in self.contrats if c.chevauche(debut, fin)]

    @property
    def contrat_en_cours(self):
        return next((c for c in reversed(self.contrats) if c.date_fin is None), None)

    @property
    def date_entree(self):
        """Début de la période d'emploi actuelle (ou de la dernière)."""
        if not self.contrats:
            return None
        debut = self.contrats[-1].date_debut
        for precedent in reversed(self.contrats[:-1]):
            if precedent.date_fin and (debut - precedent.date_fin).days == 1:
                debut = precedent.date_debut
            else:
                break
        return debut

    @property
    def date_sortie(self):
        if not self.contrats:
            return None
        return self.contrats[-1].date_fin

    def to_dict(self, avec_contrats=False):
        data = {
            'id': self.id,
            'nom': self.nom,
            'prenom': self.prenom,
            'identifiant': self.utilisateur.identifiant if self.utilisateur else None,
            'actif': bool(self.utilisateur and self.utilisateur.actif),
            'date_entree': _iso(self.date_entree),
            'date_sortie': _iso(self.date_sortie),
            'heures_mensuelles': self.contrats[-1].heures if self.contrats else None,
        }
        if avec_contrats:
            data['contrats'] = [c.to_dict() for c in self.contrats]
        return data


class Contrat(Horodatage, db.Model):
    """Période de contrat. L'historique des contrats définit les périodes d'emploi."""

    __tablename__ = 'contrats'

    id = db.Column(db.Integer, primary_key=True)
    employe_id = db.Column(db.Integer, db.ForeignKey('employes.id', ondelete='CASCADE'), nullable=False, index=True)
    heures_mensuelles = db.Column(db.Numeric(6, 2), nullable=False)
    date_debut = db.Column(db.Date, nullable=False)
    date_fin = db.Column(db.Date, nullable=True)

    employe = db.relationship('Employe', back_populates='contrats')

    __table_args__ = (
        db.CheckConstraint('heures_mensuelles > 0', name='ck_contrats_heures'),
        db.CheckConstraint('date_fin IS NULL OR date_fin >= date_debut', name='ck_contrats_dates'),
    )

    @property
    def heures(self):
        return float(self.heures_mensuelles)

    def chevauche(self, debut, fin):
        return self.date_debut <= fin and (self.date_fin is None or self.date_fin >= debut)

    def to_dict(self):
        return {
            'id': self.id,
            'heures_mensuelles': self.heures,
            'date_debut': _iso(self.date_debut),
            'date_fin': _iso(self.date_fin),
        }


class MotifAbsence(Horodatage, db.Model):
    __tablename__ = 'motifs_absence'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), nullable=False, unique=True)
    libelle = db.Column(db.String(80), nullable=False)
    couleur = db.Column(db.String(7), nullable=False, default='#6c757d')
    actif = db.Column(db.Boolean, nullable=False, default=True)
    ordre = db.Column(db.Integer, nullable=False, default=0)

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'libelle': self.libelle,
            'couleur': self.couleur,
            'actif': self.actif,
            'ordre': self.ordre,
        }


class Absence(Horodatage, db.Model):
    """Période d'absence : du premier jour d'absence (inclus) au jour de reprise (exclu)."""

    __tablename__ = 'absences'

    id = db.Column(db.Integer, primary_key=True)
    employe_id = db.Column(db.Integer, db.ForeignKey('employes.id', ondelete='CASCADE'), nullable=False, index=True)
    motif_id = db.Column(db.Integer, db.ForeignKey('motifs_absence.id'), nullable=False)
    date_debut = db.Column(db.Date, nullable=False)
    date_reprise = db.Column(db.Date, nullable=True)
    commentaire = db.Column(db.String(255), nullable=True)

    employe = db.relationship('Employe')
    motif = db.relationship('MotifAbsence')

    __table_args__ = (
        db.CheckConstraint('date_reprise IS NULL OR date_reprise > date_debut', name='ck_absences_dates'),
    )

    def couvre(self, jour):
        return self.date_debut <= jour and (self.date_reprise is None or jour < self.date_reprise)

    def touche_periode(self, debut, fin):
        return self.date_debut <= fin and (self.date_reprise is None or self.date_reprise > debut)

    def to_dict(self):
        return {
            'id': self.id,
            'employe_id': self.employe_id,
            'motif_id': self.motif_id,
            'motif_code': self.motif.code if self.motif else None,
            'motif_libelle': self.motif.libelle if self.motif else None,
            'motif_couleur': self.motif.couleur if self.motif else None,
            'date_debut': _iso(self.date_debut),
            'date_reprise': _iso(self.date_reprise),
            'commentaire': self.commentaire,
        }


class HeuresEnPlus(Horodatage, db.Model):
    __tablename__ = 'heures_en_plus'

    id = db.Column(db.Integer, primary_key=True)
    employe_id = db.Column(db.Integer, db.ForeignKey('employes.id', ondelete='CASCADE'), nullable=False)
    jour = db.Column(db.Date, nullable=False)
    heures = db.Column(db.Numeric(5, 2), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('employe_id', 'jour', name='uq_heures_employe_jour'),
        db.CheckConstraint('heures > 0 AND heures <= 24', name='ck_heures_bornes'),
        db.CheckConstraint('heures * 4 = floor(heures * 4)', name='ck_heures_quart'),
    )

    def to_dict(self):
        return {'id': self.id, 'employe_id': self.employe_id, 'jour': _iso(self.jour), 'heures': float(self.heures)}


class Deplacement(Horodatage, db.Model):
    __tablename__ = 'deplacements'

    EN_ATTENTE = 'en_attente'
    VALIDE = 'valide'
    REFUSE = 'refuse'

    id = db.Column(db.Integer, primary_key=True)
    employe_id = db.Column(db.Integer, db.ForeignKey('employes.id', ondelete='CASCADE'), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False)
    depart = db.Column(db.String(120), nullable=False)
    arrivee = db.Column(db.String(120), nullable=False)
    motif = db.Column(db.String(255), nullable=False)
    km = db.Column(db.Numeric(7, 1), nullable=False)
    statut = db.Column(db.String(12), nullable=False, default=EN_ATTENTE)
    motif_refus = db.Column(db.String(255), nullable=True)
    valide_par_id = db.Column(db.Integer, db.ForeignKey('utilisateurs.id', ondelete='SET NULL'), nullable=True)
    valide_le = db.Column(db.DateTime(timezone=True), nullable=True)

    employe = db.relationship('Employe')

    __table_args__ = (
        db.CheckConstraint('km > 0', name='ck_deplacements_km'),
        db.CheckConstraint("statut IN ('en_attente', 'valide', 'refuse')", name='ck_deplacements_statut'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'employe_id': self.employe_id,
            'employe_nom': self.employe.nom if self.employe else None,
            'employe_prenom': self.employe.prenom if self.employe else None,
            'date': _iso(self.date),
            'depart': self.depart,
            'arrivee': self.arrivee,
            'motif': self.motif,
            'km': float(self.km),
            'statut': self.statut,
            'motif_refus': self.motif_refus,
            'valide_le': _iso(self.valide_le),
        }


class JourFermeture(Horodatage, db.Model):
    __tablename__ = 'jours_fermeture'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, unique=True)
    libelle = db.Column(db.String(120), nullable=True)

    def to_dict(self):
        return {'id': self.id, 'date': _iso(self.date), 'libelle': self.libelle}

