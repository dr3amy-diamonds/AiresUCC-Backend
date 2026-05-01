"""
Modelo para la tabla de Bloques (Edificios).
Representa los edificios físicos de la UCC Montería.
"""

from sqlalchemy import Column, Integer, String, UniqueConstraint
from app.db.base_class import Base


class Bloque(Base):
    """
    Modelo SQLAlchemy para la tabla 'bloques'.
    Representa los edificios físicos de la universidad.

    Atributos:
        id (int): Identificador único del bloque (clave primaria).
        codigo_bloque (str): Código único del edificio (ej: 'B1', 'B_ADM').
        nombre_bloque (str): Nombre descriptivo del edificio (ej: 'Bloque 1', 'Bloque Administrativo').
    """

    __tablename__ = "bloques"

    id: int = Column(Integer, primary_key=True, index=True)
    codigo_bloque: str = Column(String(15), nullable=False, unique=True, index=True)
    nombre_bloque: str = Column(String(65), nullable=False, unique=True, index=True)

    # Restricciones
    __table_args__ = (
        UniqueConstraint('codigo_bloque', name='uq_bloque_codigo'),
        UniqueConstraint('nombre_bloque', name='uq_bloque_nombre'),
        {"schema": "gestion_aires_ucc"}
    )

