"""Planning de présence : une seule trame par personne, sans date de début.

On garde la trame en vigueur aujourd'hui (sinon la plus ancienne) ; les autres sont supprimées.

Revision ID: 0010
Revises: 0009
Create Date: 2026-11-27 07:30:00

"""
from datetime import date

from alembic import op
import sqlalchemy as sa


revision = '0010'
down_revision = '0009'
branch_labels = None
depends_on = None


def upgrade():
    connexion = op.get_bind()
    gardees = {}
    lignes = connexion.execute(
        sa.text('SELECT id, employe_id, utilisateur_id, date_debut FROM trames_planning ORDER BY date_debut, id')
    ).fetchall()
    aujourdhui = date.today()
    for id_, employe_id, utilisateur_id, date_debut in lignes:
        cle = ('employe', employe_id) if employe_id is not None else ('admin', utilisateur_id)
        if cle not in gardees or date_debut <= aujourdhui:
            gardees[cle] = id_
    if gardees:
        connexion.execute(
            sa.text('DELETE FROM trames_planning WHERE id NOT IN :ids').bindparams(sa.bindparam('ids', expanding=True)),
            {'ids': list(gardees.values())},
        )
    else:
        connexion.execute(sa.text('DELETE FROM trames_planning'))

    op.drop_constraint('uq_trames_planning_employe_debut', 'trames_planning', type_='unique')
    op.drop_constraint('uq_trames_planning_utilisateur_debut', 'trames_planning', type_='unique')
    op.drop_column('trames_planning', 'date_debut')
    op.create_unique_constraint('uq_trames_planning_employe', 'trames_planning', ['employe_id'])
    op.create_unique_constraint('uq_trames_planning_utilisateur', 'trames_planning', ['utilisateur_id'])


def downgrade():
    op.drop_constraint('uq_trames_planning_employe', 'trames_planning', type_='unique')
    op.drop_constraint('uq_trames_planning_utilisateur', 'trames_planning', type_='unique')
    op.add_column('trames_planning', sa.Column('date_debut', sa.Date(), nullable=False, server_default='2000-01-01'))
    op.alter_column('trames_planning', 'date_debut', server_default=None)
    op.create_unique_constraint('uq_trames_planning_employe_debut', 'trames_planning', ['employe_id', 'date_debut'])
    op.create_unique_constraint('uq_trames_planning_utilisateur_debut', 'trames_planning', ['utilisateur_id', 'date_debut'])
