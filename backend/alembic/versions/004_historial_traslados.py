"""Create historial_traslados table.

Revision ID: 004_historial_traslados
Revises: 003_tipos_gas_refrigerante
Create Date: 2026-10-22
"""

from alembic import op
import sqlalchemy as sa


revision = "004_historial_traslados"
down_revision = "003_tipos_gas_refrigerante"
branch_labels = None
depends_on = None

SCHEMA = "gestion_aires_ucc"


def upgrade() -> None:
    op.create_table(
        "historial_traslados",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("equipo_id", sa.Integer(), nullable=False),
        sa.Column("espacio_origen_id", sa.Integer(), nullable=True),
        sa.Column("espacio_destino_id", sa.Integer(), nullable=False),
        sa.Column("encargado_id", sa.Integer(), nullable=False),
        sa.Column(
            "fecha_traslado",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["equipo_id"],
            [f"{SCHEMA}.equipos.id"],
            name="fk_historial_traslados_equipo_id",
        ),
        sa.ForeignKeyConstraint(
            ["espacio_origen_id"],
            [f"{SCHEMA}.espacios.id"],
            name="fk_historial_traslados_espacio_origen_id",
        ),
        sa.ForeignKeyConstraint(
            ["espacio_destino_id"],
            [f"{SCHEMA}.espacios.id"],
            name="fk_historial_traslados_espacio_destino_id",
        ),
        sa.ForeignKeyConstraint(
            ["encargado_id"],
            [f"{SCHEMA}.encargados.id"],
            name="fk_historial_traslados_encargado_id",
        ),
        sa.PrimaryKeyConstraint("id"),
        schema=SCHEMA,
    )
    op.create_index(
        op.f("ix_gestion_aires_ucc_historial_traslados_id"),
        "historial_traslados",
        ["id"],
        unique=False,
        schema=SCHEMA,
    )
    op.create_index(
        op.f("ix_gestion_aires_ucc_historial_traslados_equipo_id"),
        "historial_traslados",
        ["equipo_id"],
        unique=False,
        schema=SCHEMA,
    )
    op.create_index(
        op.f("ix_gestion_aires_ucc_historial_traslados_espacio_origen_id"),
        "historial_traslados",
        ["espacio_origen_id"],
        unique=False,
        schema=SCHEMA,
    )
    op.create_index(
        op.f("ix_gestion_aires_ucc_historial_traslados_espacio_destino_id"),
        "historial_traslados",
        ["espacio_destino_id"],
        unique=False,
        schema=SCHEMA,
    )
    op.create_index(
        op.f("ix_gestion_aires_ucc_historial_traslados_encargado_id"),
        "historial_traslados",
        ["encargado_id"],
        unique=False,
        schema=SCHEMA,
    )
    op.create_index(
        op.f("ix_gestion_aires_ucc_historial_traslados_fecha_traslado"),
        "historial_traslados",
        ["fecha_traslado"],
        unique=False,
        schema=SCHEMA,
    )


def downgrade() -> None:
    for index_name in (
        "ix_gestion_aires_ucc_historial_traslados_fecha_traslado",
        "ix_gestion_aires_ucc_historial_traslados_encargado_id",
        "ix_gestion_aires_ucc_historial_traslados_espacio_destino_id",
        "ix_gestion_aires_ucc_historial_traslados_espacio_origen_id",
        "ix_gestion_aires_ucc_historial_traslados_equipo_id",
        "ix_gestion_aires_ucc_historial_traslados_id",
    ):
        op.drop_index(index_name, table_name="historial_traslados", schema=SCHEMA)
    op.drop_table("historial_traslados", schema=SCHEMA)
