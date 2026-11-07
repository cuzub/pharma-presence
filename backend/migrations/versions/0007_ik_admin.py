"""Indemnités kilométriques des admins.

Revision ID: 0007
Revises: 0006
Create Date: 2026-11-07 15:00:00

"""
from alembic import op
import sqlalchemy as sa


revision = '0007'
down_revision = '0006'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('utilisateurs', sa.Column('nom_affiche', sa.String(100), nullable=True))

    op.alter_column('deplacements', 'employe_id', existing_type=sa.Integer(), nullable=True)
    op.add_column('deplacements', sa.Column('utilisateur_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_deplacements_utilisateur', 'deplacements', 'utilisateurs', ['utilisateur_id'], ['id'], ondelete='CASCADE')
    op.create_index('ix_deplacements_utilisateur_id', 'deplacements', ['utilisateur_id'])
    op.create_check_constraint('ck_deplacements_titulaire', 'deplacements', '(employe_id IS NULL) <> (utilisateur_id IS NULL)')

    op.add_column('journal_modifications', sa.Column('admin_concerne_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_journal_admin_concerne', 'journal_modifications', 'utilisateurs', ['admin_concerne_id'], ['id'], ondelete='SET NULL')

    op.create_table(
        'parametres_ik',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('coefficient', sa.Numeric(6, 3), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_by_id', sa.Integer(), sa.ForeignKey('utilisateurs.id', ondelete='SET NULL'), nullable=True),
        sa.CheckConstraint('id = 1', name='ck_parametres_ik_singleton'),
    )


def downgrade():
    op.drop_table('parametres_ik')
    op.drop_constraint('fk_journal_admin_concerne', 'journal_modifications', type_='foreignkey')
    op.drop_column('journal_modifications', 'admin_concerne_id')
    op.execute('DELETE FROM deplacements WHERE utilisateur_id IS NOT NULL')
    op.drop_constraint('ck_deplacements_titulaire', 'deplacements', type_='check')
    op.drop_index('ix_deplacements_utilisateur_id', table_name='deplacements')
    op.drop_constraint('fk_deplacements_utilisateur', 'deplacements', type_='foreignkey')
    op.drop_column('deplacements', 'utilisateur_id')
    op.alter_column('deplacements', 'employe_id', existing_type=sa.Integer(), nullable=False)
    op.drop_column('utilisateurs', 'nom_affiche')
