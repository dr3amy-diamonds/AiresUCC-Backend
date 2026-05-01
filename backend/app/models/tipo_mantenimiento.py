"""
Modelo para la tabla de Tipos de Mantenimiento.
Define si es preventivo, correctivo, etc. Base para la generación automática de cronogramas.
"""

from sqlalchemy import Column, Integer, String, UniqueConstraint
from app.db.base_class import Base


class TipoMantenimiento(Base):
    """
    Modelo SQLAlchemy para la tabla 'tipos_mantenimiento'.
    Clasificación de trabajos de mantenimiento.

    Atributos:
        id (int): Identificador único del tipo (clave primaria).
        nombre (str): Nombre del tipo (ej: 'Preventivo', 'Correctivo', 'Inspección').
        frecuencia_dias (int): Días recomendados entre mantenimientos (usado por API para cronogramas).
    """

    __tablename__ = "tipos_mantenimiento"

    id: int = Column(Integer, primary_key=True, index=True)
    nombre: str = Column(String(30), nullable=False, unique=True, index=True)
    frecuencia_dias: int = Column(Integer, nullable=True)

    # Restricciones
    __table_args__ = (
        UniqueConstraint('nombre', name='uq_tipo_mantenimiento_nombre'),
        {"schema": "gestion_aires_ucc"}
    )

