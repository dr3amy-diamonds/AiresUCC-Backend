"""
Modelo para la tabla de Equipos de aire acondicionado.
El activo central del sistema. Cada registro es un aire físico real en la universidad.
"""

from typing import Optional
from datetime import date, datetime
from sqlalchemy import Column, Integer, String, Date, ForeignKey, Enum, DateTime, func
from sqlalchemy.orm import relationship
from app.db.base_class import Base
import enum


class EstadoEquipo(str, enum.Enum):
    """Estados posibles de un equipo de aire acondicionado."""
    OPERATIVO = "Operativo"
    EN_REPARACION = "En reparacion"
    INACTIVO = "Inactivo"
    DADO_DE_BAJA = "Dado de baja"


class Equipo(Base):
    """
    Modelo SQLAlchemy para la tabla 'equipo'.
    Representa los equipos de aire acondicionado instalados en la universidad.

    Atributos:
        id (int): Identificador único del equipo (clave primaria).
        serial (str): Número de serie único del fabricante.
        modelo (str): Modelo del equipo (ej: 'LG AS-W12GQLDG0').
        fecha_instalacion (date): Fecha de instalación del equipo.
        marca_id (int): FK a la tabla marcas.
        espacio_id (int): FK a la tabla espacios.
        estado (EstadoEquipo): Estado actual del equipo (Operativo, En reparación, Inactivo, Dado de baja).
        created_at (datetime): Timestamp de creación del registro.
        updated_at (datetime): Timestamp de última actualización.
    """

    __tablename__ = "equipos"

    # Columnas
    id: int = Column(Integer, primary_key=True, index=True)
    serial: str = Column(String(50), nullable=False, unique=True, index=True)
    modelo: str = Column(String(50), nullable=True)
    fecha_instalacion: Optional[date] = Column(Date, nullable=True)
    estado: EstadoEquipo = Column(
        Enum(EstadoEquipo),
        default=EstadoEquipo.OPERATIVO,
        nullable=False
    )
    created_at: datetime = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at: datetime = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Claves foráneas
    marca_id: int = Column(Integer, ForeignKey("marcas.id"), nullable=False, index=True)
    espacio_id: int = Column(Integer, ForeignKey("espacios.id"), nullable=False, index=True)

    # Relaciones
    marca = relationship("Marca", backref="equipos")
    espacio = relationship("Espacio", backref="equipos")
