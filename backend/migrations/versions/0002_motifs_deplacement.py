"""Motifs de déplacement (destination + km) ; suppression des champs départ / arrivée.

Les déplacements existants deviennent des « Autre » : le trajet est conservé dans le motif.

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-31 11:00:00

"""
from alembic import op
import sqlalchemy as sa


revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('motifs_deplacement',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('libelle', sa.String(length=80), nullable=False),
    sa.Column('km', sa.Numeric(precision=7, scale=1), nullable=False),
    sa.Column('actif', sa.Boolean(), nullable=False),
    sa.Column('ordre', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_by_id', sa.Integer(), nullable=True),
    sa.CheckConstraint('km > 0', name='ck_motifs_deplacement_km'),
    sa.ForeignKeyConstraint(['updated_by_id'], ['utilisateurs.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('libelle')
    )

    op.execute(
        "UPDATE deplacements SET motif = left(motif || ' (' || depart || ' → ' || arrivee || ')', 255)"
    )
    with op.batch_alter_table('deplacements', schema=None) as batch_op:
        batch_op.add_column(sa.Column('motif_deplacement_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_deplacements_motif_deplacement', 'motifs_deplacement', ['motif_deplacement_id'], ['id'])
        batch_op.drop_column('depart')
        batch_op.drop_column('arrivee')


def downgrade():
    with op.batch_alter_table('deplacements', schema=None) as batch_op:
        batch_op.add_column(sa.Column('arrivee', sa.String(length=120), nullable=False, server_default=''))
        batch_op.add_column(sa.Column('depart', sa.String(length=120), nullable=False, server_default=''))
        batch_op.drop_constraint('fk_deplacements_motif_deplacement', type_='foreignkey')
        batch_op.drop_column('motif_deplacement_id')

    op.drop_table('motifs_deplacement')
