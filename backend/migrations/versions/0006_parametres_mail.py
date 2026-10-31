"""Paramètres d'envoi de l'export par mail (destinataire, titre, texte).

Revision ID: 0006
Revises: 0005
Create Date: 2026-10-31 18:00:00

"""
from alembic import op
import sqlalchemy as sa


revision = '0006'
down_revision = '0005'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'parametres_mail',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('destinataire', sa.String(254), nullable=False),
        sa.Column('titre', sa.String(200), nullable=False),
        sa.Column('texte', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_by_id', sa.Integer(), sa.ForeignKey('utilisateurs.id', ondelete='SET NULL'), nullable=True),
        sa.CheckConstraint('id = 1', name='ck_parametres_mail_singleton'),
    )


def downgrade():
    op.drop_table('parametres_mail')
