"""Revision ID: 002_audit_business_events
Revises: 001_add_fecha_compra
Create Date: 2026-06-12

Regla de negocio: columnas de auditoría de negocio con snapshot y narrativa.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "002_audit_business_events"
down_revision: Union[str, None] = "001_add_fecha_compra"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "auditoria",
        sa.Column("tipo_evento", sa.String(40), nullable=True),
        schema="gestion_aires_ucc",
    )
    op.add_column(
        "auditoria",
        sa.Column("actor_nombre", sa.String(120), nullable=True),
        schema="gestion_aires_ucc",
    )
    op.add_column(
        "auditoria",
        sa.Column("actor_rol", sa.String(60), nullable=True),
        schema="gestion_aires_ucc",
    )
    op.add_column(
        "auditoria",
        sa.Column("actor_rol_etiqueta", sa.String(80), nullable=True),
        schema="gestion_aires_ucc",
    )
    op.add_column(
        "auditoria",
        sa.Column("ubicacion_snapshot", sa.Text(), nullable=True),
        schema="gestion_aires_ucc",
    )
    op.add_column(
        "auditoria",
        sa.Column("recurso_descripcion", sa.String(200), nullable=True),
        schema="gestion_aires_ucc",
    )
    op.add_column(
        "auditoria",
        sa.Column("narrativa", sa.Text(), nullable=True),
        schema="gestion_aires_ucc",
    )
    op.add_column(
        "auditoria",
        sa.Column("justificacion", sa.Text(), nullable=True),
        schema="gestion_aires_ucc",
    )


def downgrade() -> None:
    for col in (
        "justificacion",
        "narrativa",
        "recurso_descripcion",
        "ubicacion_snapshot",
        "actor_rol_etiqueta",
        "actor_rol",
        "actor_nombre",
        "tipo_evento",
    ):
        op.drop_column("auditoria", col, schema="gestion_aires_ucc")
