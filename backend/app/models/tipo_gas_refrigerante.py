"""
Modelo para la tabla de Tipos de Gas Refrigerante.
Catálogo de gases refrigerantes utilizados en equipos de climatización.
"""

from sqlalchemy import Column, Integer, String, UniqueConstraint
from app.db.base_class import Base


class TipoGasRefrigerante(Base):
    """Catálogo de tipos de gas refrigerante (ej: R410A, R32)."""

    __tablename__ = "tipos_gas_refrigerante"

    id: int = Column(Integer, primary_key=True, index=True)
    nombre: str = Column(String(20), nullable=False, unique=True, index=True)

    __table_args__ = (
        UniqueConstraint("nombre", name="uq_tipo_gas_refrigerante_nombre"),
        {"schema": "gestion_aires_ucc"},
    )
