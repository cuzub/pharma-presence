"""Régularisations d'heures +/- : crédits et débits saisis par la pharmacienne.

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-31 15:00:00

"""
from alembic import op
import sqlalchemy as sa


revision = '0005'
down_revision = '0004'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'regularisations_heures',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('employe_id', sa.Integer(), sa.ForeignKey('employes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('jour', sa.Date(), nullable=False),
        sa.Column('minutes', sa.Integer(), nullable=False),
        sa.Column('commentaire', sa.String(200), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_by_id', sa.Integer(), sa.ForeignKey('utilisateurs.id', ondelete='SET NULL'), nullable=True),
        sa.CheckConstraint('minutes <> 0 AND minutes BETWEEN -30000 AND 30000', name='ck_regularisation_minutes_bornes'),
        sa.CheckConstraint('minutes % 5 = 0', name='ck_regularisation_minutes_pas'),
    )
    op.create_index('ix_regularisations_heures_employe_id', 'regularisations_heures', ['employe_id'])

    op.alter_column('journal_modifications', 'type', type_=sa.String(20), existing_type=sa.String(12), existing_nullable=False)
    op.drop_constraint('ck_journal_type', 'journal_modifications', type_='check')
    op.create_check_constraint(
        'ck_journal_type', 'journal_modifications', "type IN ('deplacement', 'heures', 'absence', 'regularisation')"
    )


def downgrade():
    op.execute("DELETE FROM journal_modifications WHERE type = 'regularisation'")
    op.drop_constraint('ck_journal_type', 'journal_modifications', type_='check')
    op.create_check_constraint('ck_journal_type', 'journal_modifications', "type IN ('deplacement', 'heures', 'absence')")
    op.alter_column('journal_modifications', 'type', type_=sa.String(12), existing_type=sa.String(20), existing_nullable=False)
    op.drop_index('ix_regularisations_heures_employe_id', table_name='regularisations_heures')
    op.drop_table('regularisations_heures')
