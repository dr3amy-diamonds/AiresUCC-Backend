"""
Modelo para Componentes Usados.
Tabla puente: detalle de los repuestos consumidos en cada mantenimiento.
Crucial para costear cada mantenimiento y proyectar presupuestos.
"""

from decimal import Decimal
from sqlalchemy import Column, Integer, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class ComponenteUsado(Base):
    """
    Modelo SQLAlchemy para la tabla 'componentes_usados'.
    Registro de repuestos utilizados en mantenimientos (tabla puente).

    Atributos:
        id (int): Identificador único (clave primaria).
        cantidad (Decimal): Cantidad de repuesto utilizado (ej: 2.5 litros).
        precio_unitario (Decimal): Precio en el momento del uso (para histórico de costos).
        mantenimiento_realizado_id (int): FK a mantenimientos - trabajo donde se usó el repuesto.
        repuesto_utilizado_id (int): FK a tipos_componentes - tipo de repuesto.
    """

    __tablename__ = "componentes_usados"

    id: int = Column(Integer, primary_key=True, index=True)
    cantidad: Decimal = Column(Numeric(3, 1), nullable=False)
    precio_unitario: Decimal = Column(Numeric(10, 2), nullable=True)

    # Claves foráneas
    mantenimiento_realizado_id: int = Column(Integer, ForeignKey("gestion_aires_ucc.mantenimientos.id"), nullable=False, index=True)
    repuesto_utilizado_id: int = Column(Integer, ForeignKey("gestion_aires_ucc.tipos_componentes.id"), nullable=False, index=True)

    # Relaciones
    mantenimiento = relationship("Mantenimiento", backref="componentes_usados")
    componente = relationship("TipoComponente", backref="usos")

    __table_args__ = {"schema": "gestion_aires_ucc"}

