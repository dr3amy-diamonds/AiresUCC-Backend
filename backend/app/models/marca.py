"""
Modelo para la tabla de Marcas de equipos de aire acondicionado.
Catálogo de fabricantes para estandarizar el registro y facilitar filtros en el frontend.
"""

from sqlalchemy import Column, Integer, String, UniqueConstraint
from app.db.base_class import Base


class Marca(Base):
    """
    Modelo SQLAlchemy para la tabla 'marca'.
    Representa los fabricantes de equipos de aire acondicionado.

    Atributos:
        id (int): Identificador único de la marca (clave primaria).
        nombre (str): Nombre del fabricante (único, ejemplo: 'LG', 'Samsung', 'Fujitsu').
    """

    __tablename__ = "marcas"

    # Columnas
    id: int = Column(Integer, primary_key=True, index=True)
    nombre: str = Column(String(20), nullable=False, unique=True, index=True)

    # Restricciones
    __table_args__ = (
        UniqueConstraint('nombre', name='uq_marca_nombre'),
    )
