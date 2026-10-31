"""Motifs d'absence bloquants : pendant une absence, pas d'heures ni de déplacements.

Par défaut, tous les motifs existants bloquent la saisie. La formation et « Autre » ne la bloquent pas.

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-31 13:00:00

"""
from alembic import op
import sqlalchemy as sa


revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'motifs_absence',
        sa.Column('bloque_saisie', sa.Boolean(), server_default=sa.true(), nullable=False),
    )
    op.execute("UPDATE motifs_absence SET bloque_saisie = false WHERE code IN ('FORM', 'AUTRE')")


def downgrade():
    op.drop_column('motifs_absence', 'bloque_saisie')
