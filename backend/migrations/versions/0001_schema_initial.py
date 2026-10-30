"""Schéma initial : tables, contraintes anti-chevauchement et motifs d'absence par défaut.

Revision ID: 0001
Revises: 
Create Date: 2026-10-30 21:31:16.199391

"""
from datetime import datetime, timezone

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


MOTIFS_PAR_DEFAUT = [
    ('CP', 'Congés payés', '#0d6efd'),
    ('MAL', 'Maladie', '#dc3545'),
    ('RECUP', 'Récupération', '#20c997'),
    ('MAT', 'Congé maternité', '#d63384'),
    ('PAT', 'Congé paternité', '#6f42c1'),
    ('SS', 'Sans solde', '#fd7e14'),
    ('FORM', 'Formation', '#0dcaf0'),
    ('AUTRE', 'Autre', '#6c757d'),
]


def upgrade():
    # Nécessaire pour combiner « employe_id = » et « daterange && » dans une contrainte d'exclusion.
    op.execute('CREATE EXTENSION IF NOT EXISTS btree_gist')

    op.create_table('utilisateurs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('identifiant', sa.String(length=80), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('role', sa.String(length=10), nullable=False),
    sa.Column('actif', sa.Boolean(), nullable=False),
    sa.Column('doit_changer_mdp', sa.Boolean(), nullable=False),
    sa.Column('version_session', sa.Integer(), nullable=False),
    sa.Column('derniere_connexion', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_by_id', sa.Integer(), nullable=True),
    sa.CheckConstraint("role IN ('admin', 'employe')", name='ck_utilisateurs_role'),
    sa.ForeignKeyConstraint(['updated_by_id'], ['utilisateurs.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('identifiant')
    )
    op.create_table('employes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('utilisateur_id', sa.Integer(), nullable=True),
    sa.Column('nom', sa.String(length=100), nullable=False),
    sa.Column('prenom', sa.String(length=100), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_by_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['updated_by_id'], ['utilisateurs.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['utilisateur_id'], ['utilisateurs.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('utilisateur_id')
    )
    op.create_table('jours_fermeture',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('libelle', sa.String(length=120), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_by_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['updated_by_id'], ['utilisateurs.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('date')
    )
    op.create_table('motifs_absence',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(length=20), nullable=False),
    sa.Column('libelle', sa.String(length=80), nullable=False),
    sa.Column('couleur', sa.String(length=7), nullable=False),
    sa.Column('actif', sa.Boolean(), nullable=False),
    sa.Column('ordre', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_by_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['updated_by_id'], ['utilisateurs.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code')
    )
    op.create_table('absences',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('employe_id', sa.Integer(), nullable=False),
    sa.Column('motif_id', sa.Integer(), nullable=False),
    sa.Column('date_debut', sa.Date(), nullable=False),
    sa.Column('date_reprise', sa.Date(), nullable=True),
    sa.Column('commentaire', sa.String(length=255), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_by_id', sa.Integer(), nullable=True),
    sa.CheckConstraint('date_reprise IS NULL OR date_reprise > date_debut', name='ck_absences_dates'),
    sa.ForeignKeyConstraint(['employe_id'], ['employes.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['motif_id'], ['motifs_absence.id'], ),
    sa.ForeignKeyConstraint(['updated_by_id'], ['utilisateurs.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('absences', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_absences_employe_id'), ['employe_id'], unique=False)

    op.create_table('contrats',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('employe_id', sa.Integer(), nullable=False),
    sa.Column('heures_mensuelles', sa.Numeric(precision=6, scale=2), nullable=False),
    sa.Column('date_debut', sa.Date(), nullable=False),
    sa.Column('date_fin', sa.Date(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_by_id', sa.Integer(), nullable=True),
    sa.CheckConstraint('date_fin IS NULL OR date_fin >= date_debut', name='ck_contrats_dates'),
    sa.CheckConstraint('heures_mensuelles > 0', name='ck_contrats_heures'),
    sa.ForeignKeyConstraint(['employe_id'], ['employes.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['updated_by_id'], ['utilisateurs.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('contrats', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_contrats_employe_id'), ['employe_id'], unique=False)

    op.create_table('deplacements',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('employe_id', sa.Integer(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('depart', sa.String(length=120), nullable=False),
    sa.Column('arrivee', sa.String(length=120), nullable=False),
    sa.Column('motif', sa.String(length=255), nullable=False),
    sa.Column('km', sa.Numeric(precision=7, scale=1), nullable=False),
    sa.Column('statut', sa.String(length=12), nullable=False),
    sa.Column('motif_refus', sa.String(length=255), nullable=True),
    sa.Column('valide_par_id', sa.Integer(), nullable=True),
    sa.Column('valide_le', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_by_id', sa.Integer(), nullable=True),
    sa.CheckConstraint("statut IN ('en_attente', 'valide', 'refuse')", name='ck_deplacements_statut'),
    sa.CheckConstraint('km > 0', name='ck_deplacements_km'),
    sa.ForeignKeyConstraint(['employe_id'], ['employes.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['updated_by_id'], ['utilisateurs.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['valide_par_id'], ['utilisateurs.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('deplacements', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_deplacements_employe_id'), ['employe_id'], unique=False)

    op.create_table('heures_en_plus',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('employe_id', sa.Integer(), nullable=False),
    sa.Column('jour', sa.Date(), nullable=False),
    sa.Column('heures', sa.Numeric(precision=5, scale=2), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_by_id', sa.Integer(), nullable=True),
    sa.CheckConstraint('heures * 4 = floor(heures * 4)', name='ck_heures_quart'),
    sa.CheckConstraint('heures > 0 AND heures <= 24', name='ck_heures_bornes'),
    sa.ForeignKeyConstraint(['employe_id'], ['employes.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['updated_by_id'], ['utilisateurs.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('employe_id', 'jour', name='uq_heures_employe_jour')
    )
    # ### end Alembic commands ###

    # Un employé ne peut pas avoir deux contrats sur la même période.
    op.execute(
        "ALTER TABLE contrats ADD CONSTRAINT ex_contrats_chevauchement "
        "EXCLUDE USING gist (employe_id WITH =, daterange(date_debut, date_fin, '[]') WITH &&)"
    )
    # Un employé ne peut pas avoir deux absences le même jour (jour de reprise exclu).
    op.execute(
        "ALTER TABLE absences ADD CONSTRAINT ex_absences_chevauchement "
        "EXCLUDE USING gist (employe_id WITH =, daterange(date_debut, date_reprise, '[)') WITH &&)"
    )

    motifs = sa.table(
        'motifs_absence',
        sa.column('code', sa.String), sa.column('libelle', sa.String), sa.column('couleur', sa.String),
        sa.column('actif', sa.Boolean), sa.column('ordre', sa.Integer),
        sa.column('created_at', sa.DateTime(timezone=True)), sa.column('updated_at', sa.DateTime(timezone=True)),
    )
    maintenant = datetime.now(timezone.utc)
    op.bulk_insert(motifs, [
        {'code': code, 'libelle': libelle, 'couleur': couleur, 'actif': True, 'ordre': ordre,
         'created_at': maintenant, 'updated_at': maintenant}
        for ordre, (code, libelle, couleur) in enumerate(MOTIFS_PAR_DEFAUT, start=1)
    ])


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('heures_en_plus')
    with op.batch_alter_table('deplacements', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_deplacements_employe_id'))

    op.drop_table('deplacements')
    with op.batch_alter_table('contrats', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_contrats_employe_id'))

    op.drop_table('contrats')
    with op.batch_alter_table('absences', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_absences_employe_id'))

    op.drop_table('absences')
    op.drop_table('motifs_absence')
    op.drop_table('jours_fermeture')
    op.drop_table('employes')
    op.drop_table('utilisateurs')
    # ### end Alembic commands ###
