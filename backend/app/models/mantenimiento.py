"""
Modelo para la tabla de Mantenimientos.
Registros de servicios técnicos y reparaciones en los aires acondicionados.
Incluye información financiera y de auditoría.
"""

from datetime import datetime, date
from typing import Optional
from decimal import Decimal
from sqlalchemy import Column, Integer, String, Date, ForeignKey, DateTime, func, Numeric, Text
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class Mantenimiento(Base):
    """
    Modelo SQLAlchemy para la tabla 'mantenimientos'.
    Registra cada intervención técnica realizada en un equipo de aire acondicionado.

    Atributos:
        id (int): Identificador único del registro de mantenimiento.
        fecha_mantenimiento (date): Fecha en que se realizó el servicio de campo.
        detalle_mantenimiento (str): Descripción técnica de lo hallado y trabajos realizados.
        costo_servicio (Decimal): Valor económico del servicio técnico (CAMPO FINANCIERO).
        equipo_id (int): FK a la tabla de equipos (aire acondicionado intervenido).
        encargado_id (int): FK a tabla de usuarios (técnico que realizó el servicio).
        tipo_mantenimiento_id (int): FK a tabla de tipos_mantenimiento (Preventivo/Correctivo).
        registrado_por (int): FK a tabla de usuarios (quien registra en el sistema).
        created_at (datetime): Timestamp automático de creación del registro.
    """

    __tablename__ = "mantenimientos"
    __table_args__ = {"schema": "gestion_aires_ucc"}

    # Columnas principales
    id: int = Column(Integer, primary_key=True, index=True)
    fecha_mantenimiento: date = Column(Date, nullable=False, index=True)
    detalle_mantenimiento: Optional[str] = Column(Text, nullable=True)

    # --- CAMPO FINANCIERO ---
    costo_servicio: Decimal = Column(Numeric(12, 2), default=Decimal('0.00'), nullable=False)

    # Claves foráneas
    equipo_id: int = Column(Integer, ForeignKey("gestion_aires_ucc.equipos.id"), nullable=False, index=True)
    encargado_id: int = Column(Integer, ForeignKey("gestion_aires_ucc.encargados.id"), nullable=False, index=True)
    tipo_mantenimiento_id = Column(Integer, ForeignKey("gestion_aires_ucc.tipos_mantenimiento.id"), nullable=False)
    registrado_por: int = Column(Integer, ForeignKey("gestion_aires_ucc.encargados.id"), nullable=False, index=True)

    # Timestamps de auditoría
    created_at: datetime = Column(DateTime, server_default=func.now(), nullable=False)

    # Relaciones de navegación
    equipo = relationship("Equipo", backref="mantenimientos", foreign_keys=[equipo_id])
    encargado = relationship("Usuario", foreign_keys=[encargado_id], backref="mantenimientos_realizados")
    registrador = relationship("Usuario", foreign_keys=[registrado_por], backref="mantenimientos_registrados")
    tipo = relationship("TipoMantenimiento", backref="mantenimientos_tipo")
