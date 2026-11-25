"""Planning de présence : couleur des employés, trames semaine 1 / semaine 2 et exceptions à la journée.

Revision ID: 0008
Revises: 0007
Create Date: 2026-11-24 21:00:00

"""
from alembic import op
import sqlalchemy as sa


revision = '0008'
down_revision = '0007'
branch_labels = None
depends_on = None

_PALETTE = ['#e57373', '#81c784', '#ffb74d', '#ba68c8', '#f06292', '#aed581', '#ffd54f', '#a1887f', '#7986cb', '#dce775']


def _horodatage():
    return [
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_by_id', sa.Integer(), sa.ForeignKey('utilisateurs.id', ondelete='SET NULL'), nullable=True),
    ]


def _titulaire():
    return [
        sa.Column('employe_id', sa.Integer(), sa.ForeignKey('employes.id', ondelete='CASCADE'), nullable=True, index=True),
        sa.Column('utilisateur_id', sa.Integer(), sa.ForeignKey('utilisateurs.id', ondelete='CASCADE'), nullable=True, index=True),
    ]


def upgrade():
    op.add_column('employes', sa.Column('couleur', sa.String(7), nullable=False, server_default=_PALETTE[0]))
    connexion = op.get_bind()
    ids = [ligne[0] for ligne in connexion.execute(sa.text('SELECT id FROM employes ORDER BY id'))]
    for index, employe_id in enumerate(ids):
        connexion.execute(
            sa.text('UPDATE employes SET couleur = :couleur WHERE id = :id'),
            {'couleur': _PALETTE[index % len(_PALETTE)], 'id': employe_id},
        )

    op.create_table(
        'trames_planning',
        sa.Column('id', sa.Integer(), primary_key=True),
        *_titulaire(),
        sa.Column('date_debut', sa.Date(), nullable=False),
        sa.Column('horaires', sa.JSON(), nullable=False),
        *_horodatage(),
        sa.CheckConstraint('(employe_id IS NULL) <> (utilisateur_id IS NULL)', name='ck_trames_planning_titulaire'),
        sa.UniqueConstraint('employe_id', 'date_debut', name='uq_trames_planning_employe_debut'),
        sa.UniqueConstraint('utilisateur_id', 'date_debut', name='uq_trames_planning_utilisateur_debut'),
    )
    op.create_table(
        'exceptions_planning',
        sa.Column('id', sa.Integer(), primary_key=True),
        *_titulaire(),
        sa.Column('jour', sa.Date(), nullable=False),
        sa.Column('horaires', sa.JSON(), nullable=False),
        *_horodatage(),
        sa.CheckConstraint('(employe_id IS NULL) <> (utilisateur_id IS NULL)', name='ck_exceptions_planning_titulaire'),
        sa.UniqueConstraint('employe_id', 'jour', name='uq_exceptions_planning_employe_jour'),
        sa.UniqueConstraint('utilisateur_id', 'jour', name='uq_exceptions_planning_utilisateur_jour'),
    )


def downgrade():
    op.drop_table('exceptions_planning')
    op.drop_table('trames_planning')
    op.drop_column('employes', 'couleur')
