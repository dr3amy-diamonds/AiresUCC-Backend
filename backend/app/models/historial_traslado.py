"""
Modelo para la tabla de Historial de Traslados.
Registra cada cambio de ubicación física de un equipo para trazabilidad.
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class HistorialTraslado(Base):
    """
    Modelo SQLAlchemy para la tabla 'historial_traslados'.

    Atributos:
        id (int): Identificador único del traslado.
        equipo_id (int): FK al equipo trasladado.
        espacio_origen_id (int): FK al espacio de origen. Nullable por registros históricos.
        espacio_destino_id (int): FK al espacio de destino.
        encargado_id (int): FK al usuario que ejecutó el traslado.
        fecha_traslado (datetime): Timestamp del traslado.
    """

    __tablename__ = "historial_traslados"

    id: int = Column(Integer, primary_key=True, index=True)
    equipo_id: int = Column(
        Integer,
        ForeignKey("gestion_aires_ucc.equipos.id"),
        nullable=False,
        index=True,
    )
    espacio_origen_id: int | None = Column(
        Integer,
        ForeignKey("gestion_aires_ucc.espacios.id"),
        nullable=True,
        index=True,
    )
    espacio_destino_id: int = Column(
        Integer,
        ForeignKey("gestion_aires_ucc.espacios.id"),
        nullable=False,
        index=True,
    )
    encargado_id: int = Column(
        Integer,
        ForeignKey("gestion_aires_ucc.encargados.id"),
        nullable=False,
        index=True,
    )
    fecha_traslado: datetime = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    equipo = relationship("Equipo", foreign_keys=[equipo_id])
    espacio_origen = relationship("Espacio", foreign_keys=[espacio_origen_id])
    espacio_destino = relationship("Espacio", foreign_keys=[espacio_destino_id])
    encargado = relationship("Usuario", foreign_keys=[encargado_id])

    __table_args__ = {"schema": "gestion_aires_ucc"}
