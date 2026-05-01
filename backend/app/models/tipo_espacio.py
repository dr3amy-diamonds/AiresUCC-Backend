"""
Modelo para la tabla de Tipos de Espacios.
Categorización de lugares (Aula, Laboratorio, etc.).
"""

from sqlalchemy import Column, Integer, String, UniqueConstraint
from app.db.base_class import Base


class TipoEspacio(Base):
    """
    Modelo SQLAlchemy para la tabla 'tipos_espacios'.
    Define el uso del espacio físico (clasificación de ambientes).

    Atributos:
        id (int): Identificador único del tipo (clave primaria).
        nombre (str): Nombre del tipo de espacio (ej: 'Aula', 'Laboratorio', 'Oficina').
    """

    __tablename__ = "tipos_espacios"

    id: int = Column(Integer, primary_key=True, index=True)
    nombre: str = Column(String(50), nullable=False, unique=True, index=True)

    # Restricciones
    __table_args__ = (
        UniqueConstraint('nombre', name='uq_tipo_espacio_nombre'),
        {"schema": "gestion_aires_ucc"}
    )

