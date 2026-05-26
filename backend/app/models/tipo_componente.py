"""
Modelo para la tabla de Tipos de Componentes.
Catálogo de componentes y repuestos para sistemas de climatización.
"""

from sqlalchemy import Column, Integer, String
from app.db.base_class import Base


class TipoComponente(Base):
    """
    Modelo SQLAlchemy para la tabla 'tipos_componentes'.
    Catálogo de componentes y repuestos utilizados en mantenimientos.

    Atributos:
        id (int): Identificador único del componente (clave primaria).
        nombre (str): Nombre del componente o repuesto (ej: 'Compresor', 'Filtro', 'Válvula').
    """

    __tablename__ = "tipos_componentes"

    id: int = Column(Integer, primary_key=True, index=True)
    nombre: str = Column(String(60), nullable=False, index=True)

    # Esquema de la base de datos
    __table_args__ = ({"schema": "gestion_aires_ucc"},)

