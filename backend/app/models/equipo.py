"""
Modelo para la tabla de Equipos de aire acondicionado.
El activo central del sistema. Cada registro es un aire físico real en la universidad.
"""

from typing import Optional
from datetime import date, datetime
from sqlalchemy import Column, Integer, String, Date, ForeignKey, DateTime, func, Numeric
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class Equipo(Base):
    """
        Modelo SQLAlchemy para la tabla 'equipos'.
        Representa los equipos de aire acondicionado instalados en la universidad.

        Atributos:
            id (int): Identificador único del equipo (clave primaria).
            codigo_activo (str): Plaqueta de inventario oficial de la UCC (único).
            modelo (str): Modelo del equipo o referencia técnica del fabricante (ej: 'HCH45P17C').
            capacidad_btu (int): Capacidad en BTU - dato técnico para estimar carga térmica.
            tonelaje (float): Capacidad de refrigeración expresada en toneladas (ej: 3.58).
            numero_serie (str): Número de s erie único grabado por el fabricante en la unidad.
            fecha_instalacion (date): Fecha en la que el equipo fue montado en el campus.
            ultima_fecha (date): Fecha del último mantenimiento registrado satisfactoriamente.
            proxima_fecha (date): Fecha proyectada para la siguiente intervención preventiva.
            estado (str): Estado operativo actual (Operativo, En reparacion, Inactivo, Dado de baja).
            created_at (datetime): Timestamp de creación automática del registro.
            updated_at (datetime): Timestamp de la última modificación realizada al registro.
            marca_id (int): FK a la tabla de fabricantes (marcas).
            tipo_equipo_id (int): FK a la tabla de categorías (tipos_equipos).
            espacio_id (int): FK a la ubicación física (tabla espacios).
        """

    __tablename__ = "equipos"
    __table_args__ = {"schema": "gestion_aires_ucc"}  # Basado en tu database.sql

    # Columnas originales
    id: int = Column(Integer, primary_key=True, index=True)
    codigo_activo: str = Column(String(50), nullable=False, unique=True, index=True)
    modelo: str = Column(String(50), nullable=True)  # Usar para la Referencia Técnica
    capacidad_btu: int = Column(Integer, nullable=False)
    fecha_instalacion: Optional[date] = Column(Date, nullable=True)
    estado: str = Column(String(20), default="Operativo", nullable=False)
    created_at: datetime = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at: datetime = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # --- NUEVAS COLUMNAS PARA EL MVP (Atributos Directos) ---
    numero_serie: str = Column(String(60), nullable=True, unique=True, index=True)
    tonelaje: float = Column(Numeric(4, 2), nullable=True)  # Ejemplo: 3.58
    voltaje: Optional[int] = Column(Integer, nullable=True)  # Ejemplo: 220, 110
    refrigerante: str = Column(String(20), nullable=True)  # Ejemplo: R410A, R32, R407C
    fecha_compra: Optional[date] = Column(Date, nullable=True)
    ultima_fecha: Optional[date] = Column(Date, nullable=True)
    proxima_fecha: Optional[date] = Column(Date, nullable=True)

    # Claves foráneas (Relaciones existentes)
    marca_id: int = Column(Integer, ForeignKey("gestion_aires_ucc.marcas.id"), nullable=False, index=True)
    tipo_equipo_id: int = Column(Integer, ForeignKey("gestion_aires_ucc.tipos_equipos.id"), nullable=False, index=True)
    espacio_id: int = Column(Integer, ForeignKey("gestion_aires_ucc.espacios.id"), nullable=False, index=True)

    # Relaciones de navegación
    # En app/models/equipo.py
    marca = relationship("Marca", backref="equipos_marca", overlaps="equipos")
    tipo = relationship("TipoEquipo", backref="equipos_tipo", overlaps="equipos")
    espacio = relationship("Espacio", back_populates="equipos", overlaps="equipos_espacio")

