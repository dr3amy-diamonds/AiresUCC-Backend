"""Create tipos_gas_refrigerante catalog table.

Revision ID: 003_tipos_gas_refrigerante
Revises: 002_audit_business_events
Create Date: 2026-06-18
"""

from alembic import op
import sqlalchemy as sa


revision = "003_tipos_gas_refrigerante"
down_revision = "002_audit_business_events"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tipos_gas_refrigerante",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("nombre", sa.String(length=20), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nombre", name="uq_tipo_gas_refrigerante_nombre"),
        schema="gestion_aires_ucc",
    )
    op.create_index(
        op.f("ix_gestion_aires_ucc_tipos_gas_refrigerante_id"),
        "tipos_gas_refrigerante",
        ["id"],
        unique=False,
        schema="gestion_aires_ucc",
    )
    op.create_index(
        op.f("ix_gestion_aires_ucc_tipos_gas_refrigerante_nombre"),
        "tipos_gas_refrigerante",
        ["nombre"],
        unique=True,
        schema="gestion_aires_ucc",
    )
    op.execute(
        """
        INSERT INTO gestion_aires_ucc.tipos_gas_refrigerante (nombre) VALUES
        ('R410A'), ('R32'), ('R407C')
        ON CONFLICT (nombre) DO NOTHING
        """
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_gestion_aires_ucc_tipos_gas_refrigerante_nombre"),
        table_name="tipos_gas_refrigerante",
        schema="gestion_aires_ucc",
    )
    op.drop_index(
        op.f("ix_gestion_aires_ucc_tipos_gas_refrigerante_id"),
        table_name="tipos_gas_refrigerante",
        schema="gestion_aires_ucc",
    )
    op.drop_table("tipos_gas_refrigerante", schema="gestion_aires_ucc")
