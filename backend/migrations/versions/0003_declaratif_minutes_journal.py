"""Déplacements déclaratifs, heures +/- en minutes, journal des modifications.

- deplacements : plus de statut ni de validation (tous les déplacements comptent).
- heures_en_plus : « heures » (décimal > 0) devient « minutes » (entier signé, par 5).
- journal_modifications : trace de qui a créé / modifié / supprimé quoi.

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-31 12:00:00

"""
from alembic import op
import sqlalchemy as sa


revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade():
    # PostgreSQL supprime avec les colonnes leurs contraintes (CHECK, clé étrangère).
    with op.batch_alter_table('deplacements', schema=None) as batch_op:
        batch_op.drop_column('statut')
        batch_op.drop_column('motif_refus')
        batch_op.drop_column('valide_par_id')
        batch_op.drop_column('valide_le')

    op.add_column('heures_en_plus', sa.Column('minutes', sa.Integer(), nullable=True))
    # Arrondi au multiple de 5 le plus proche (les saisies au quart d'heure tombent juste).
    op.execute('UPDATE heures_en_plus SET minutes = (round(heures * 12) * 5)::integer')
    op.execute('DELETE FROM heures_en_plus WHERE minutes = 0')
    op.execute('UPDATE heures_en_plus SET minutes = 720 WHERE minutes > 720')
    with op.batch_alter_table('heures_en_plus', schema=None) as batch_op:
        batch_op.alter_column('minutes', nullable=False)
        batch_op.drop_column('heures')
        batch_op.create_check_constraint('ck_heures_minutes_bornes', 'minutes <> 0 AND minutes BETWEEN -720 AND 720')
        batch_op.create_check_constraint('ck_heures_minutes_pas', 'minutes % 5 = 0')

    op.create_table('journal_modifications',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('cree_le', sa.DateTime(timezone=True), nullable=False),
    sa.Column('auteur_id', sa.Integer(), nullable=True),
    sa.Column('auteur_identifiant', sa.String(length=80), nullable=False),
    sa.Column('auteur_role', sa.String(length=10), nullable=False),
    sa.Column('employe_id', sa.Integer(), nullable=True),
    sa.Column('type', sa.String(length=12), nullable=False),
    sa.Column('action', sa.String(length=12), nullable=False),
    sa.Column('objet_id', sa.Integer(), nullable=True),
    sa.Column('avant', sa.JSON(), nullable=True),
    sa.Column('apres', sa.JSON(), nullable=True),
    sa.CheckConstraint("type IN ('deplacement', 'heures', 'absence')", name='ck_journal_type'),
    sa.CheckConstraint("action IN ('creation', 'modification', 'suppression')", name='ck_journal_action'),
    sa.CheckConstraint("auteur_role IN ('admin', 'employe')", name='ck_journal_auteur_role'),
    sa.ForeignKeyConstraint(['auteur_id'], ['utilisateurs.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['employe_id'], ['employes.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('journal_modifications', schema=None) as batch_op:
        batch_op.create_index('ix_journal_modifications_cree_le', ['cree_le'], unique=False)
        batch_op.create_index('ix_journal_modifications_employe_id', ['employe_id'], unique=False)


def downgrade():
    op.drop_table('journal_modifications')

    # Les heures en moins n'existaient pas : elles sont perdues.
    op.execute('DELETE FROM heures_en_plus WHERE minutes < 0')
    op.add_column('heures_en_plus', sa.Column('heures', sa.Numeric(precision=5, scale=2), nullable=True))
    op.execute('UPDATE heures_en_plus SET heures = round(minutes / 15.0) / 4')
    op.execute('DELETE FROM heures_en_plus WHERE heures = 0')
    with op.batch_alter_table('heures_en_plus', schema=None) as batch_op:
        batch_op.alter_column('heures', nullable=False)
        batch_op.drop_column('minutes')
        batch_op.create_check_constraint('ck_heures_bornes', 'heures > 0 AND heures <= 24')
        batch_op.create_check_constraint('ck_heures_quart', 'heures * 4 = floor(heures * 4)')

    with op.batch_alter_table('deplacements', schema=None) as batch_op:
        batch_op.add_column(sa.Column('statut', sa.String(length=12), nullable=False, server_default='valide'))
        batch_op.add_column(sa.Column('motif_refus', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('valide_par_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('valide_le', sa.DateTime(timezone=True), nullable=True))
        batch_op.create_foreign_key(None, 'utilisateurs', ['valide_par_id'], ['id'], ondelete='SET NULL')
        batch_op.create_check_constraint('ck_deplacements_statut', "statut IN ('en_attente', 'valide', 'refuse')")
