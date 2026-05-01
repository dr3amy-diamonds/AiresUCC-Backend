"""
Modelo para la tabla de Equipos de aire acondicionado.
El activo central del sistema. Cada registro es un aire físico real en la universidad.
"""

from typing import Optional
from datetime import date, datetime
from sqlalchemy import Column, Integer, String, Date, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class Equipo(Base):
    """
    Modelo SQLAlchemy para la tabla 'equipos'.
    Representa los equipos de aire acondicionado instalados en la universidad.

    Atributos:
        id (int): Identificador único del equipo (clave primaria).
        codigo_activo (str): Plaqueta de inventario oficial de la UCC (único).
        modelo (str): Modelo del equipo (ej: 'LG AS-W12GQLDG0').
        capacidad_btu (int): Capacidad en BTU - dato técnico vital para estimar consumo energético.
        fecha_instalacion (date): Fecha de instalación del equipo.
        estado (str): Estado actual del equipo (Operativo, En reparación, Inactivo, Dado de baja).
        created_at (datetime): Timestamp de creación del registro.
        updated_at (datetime): Timestamp de última actualización.
        marca_id (int): FK a la tabla marcas.
        tipo_equipo_id (int): FK a la tabla tipos_equipos.
        espacio_id (int): FK a la tabla espacios.
    """

    __tablename__ = "equipos"

    # Columnas
    id: int = Column(Integer, primary_key=True, index=True)
    codigo_activo: str = Column(String(50), nullable=False, unique=True, index=True)
    modelo: str = Column(String(50), nullable=True)
    capacidad_btu: int = Column(Integer, nullable=False)
    fecha_instalacion: Optional[date] = Column(Date, nullable=True)
    estado: str = Column(String(20), default="Operativo", nullable=False)
    created_at: datetime = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at: datetime = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Claves foráneas
    marca_id: int = Column(Integer, ForeignKey("gestion_aires_ucc.marcas.id"), nullable=False, index=True)
    tipo_equipo_id: int = Column(Integer, ForeignKey("gestion_aires_ucc.tipos_equipos.id"), nullable=False, index=True)
    espacio_id: int = Column(Integer, ForeignKey("gestion_aires_ucc.espacios.id"), nullable=False, index=True)

    # Relaciones
    marca = relationship("Marca", backref="equipos")
    espacio = relationship("Espacio", back_populates="equipos")

    # Esquema de base de datos
    __table_args__ = {"schema": "gestion_aires_ucc"}

