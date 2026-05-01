"""
Modelo para la tabla de Tipos de Equipos.
Clasificación técnica de aires acondicionados (Mini-split, Central, etc.).
"""

from sqlalchemy import Column, Integer, String, UniqueConstraint
from app.db.base_class import Base


class TipoEquipo(Base):
    """
    Modelo SQLAlchemy para la tabla 'tipos_equipos'.
    Clasificación técnica de equipos de aire acondicionado.

    Atributos:
        id (int): Identificador único del tipo (clave primaria).
        nombre (str): Nombre del tipo (ej: 'Mini-split', 'Central', 'Ventana').
    """

    __tablename__ = "tipos_equipos"

    id: int = Column(Integer, primary_key=True, index=True)
    nombre: str = Column(String(30), nullable=False, unique=True, index=True)

    # Restricciones
    __table_args__ = (
        UniqueConstraint('nombre', name='uq_tipo_equipo_nombre'),
        {"schema": "gestion_aires_ucc"}
    )

