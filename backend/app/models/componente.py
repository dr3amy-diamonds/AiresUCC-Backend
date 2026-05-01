"""
Modelo para la tabla de Tipos de Componentes.
Repuestos e insumos. Permite costeo de mantenimientos y proyecciones de presupuesto.
"""

from sqlalchemy import Column, Integer, String, UniqueConstraint
from app.db.base_class import Base


class TipoComponente(Base):
    """
    Modelo SQLAlchemy para la tabla 'tipos_componentes'.
    Catálogo de repuestos e insumos utilizados en mantenimientos.

    Atributos:
        id (int): Identificador único del componente (clave primaria).
        nombre (str): Nombre del repuesto (ej: 'Filtro', 'Refrigerante', 'Compresor').
        unidad_medida (str): Unidad de medida (ej: 'unidad', 'litro', 'metro').
    """

    __tablename__ = "tipos_componentes"

    id: int = Column(Integer, primary_key=True, index=True)
    nombre: str = Column(String(60), nullable=False, unique=True, index=True)
    unidad_medida: str = Column(String(35), nullable=True, index=True)

    __table_args__ = (
        UniqueConstraint('nombre', name='uq_tipo_componente_nombre'),
        {"schema": "gestion_aires_ucc"}
    )

