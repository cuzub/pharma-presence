"""Seuils de présents à la fermeture (semaine / samedi).

Revision ID: 0009
Revises: 0008
Create Date: 2026-11-25 08:00:00

"""
from alembic import op
import sqlalchemy as sa


revision = '0009'
down_revision = '0008'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'parametres_presence',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('seuil_semaine', sa.Integer(), nullable=True),
        sa.Column('seuil_samedi', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_by_id', sa.Integer(), sa.ForeignKey('utilisateurs.id', ondelete='SET NULL'), nullable=True),
        sa.CheckConstraint('id = 1', name='ck_parametres_presence_singleton'),
    )


def downgrade():
    op.drop_table('parametres_presence')
