"""Add fecha_compra, voltaje and refrigerante columns to equipos table.

Revision ID: 001
Revises: 
Create Date: 2026-05-30 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Agregar columnas a la tabla equipos
    op.add_column(
        'equipos',
        sa.Column('fecha_compra', sa.Date(), nullable=True),
        schema='gestion_aires_ucc'
    )
    op.add_column(
        'equipos',
        sa.Column('voltaje', sa.String(20), nullable=True),
        schema='gestion_aires_ucc'
    )
    op.add_column(
        'equipos',
        sa.Column('refrigerante', sa.String(20), nullable=True),
        schema='gestion_aires_ucc'
    )


def downgrade() -> None:
    # Remover columnas de la tabla equipos
    op.drop_column(
        'equipos',
        'refrigerante',
        schema='gestion_aires_ucc'
    )
    op.drop_column(
        'equipos',
        'voltaje',
        schema='gestion_aires_ucc'
    )
    op.drop_column(
        'equipos',
        'fecha_compra',
        schema='gestion_aires_ucc'
    )
