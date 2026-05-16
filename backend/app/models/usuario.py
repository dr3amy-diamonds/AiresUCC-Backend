"""
Modelo para la tabla de Usuarios (Encargados).
Gestión del personal técnico y administrativo que interactúa con el sistema.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func, UniqueConstraint
from app.db.base_class import Base


class TipoRol(str, Enum):
    """
    Roles disponibles en el sistema.

    Solo 3 roles permitidos:
    - Jefe de Infraestructura: Máximos privilegios (Admin)
    - Auxiliar de Infraestructura: Privilegios limitados
    - Tecnico: Técnico operativo
    """
    JEFE_INFRAESTRUCTURA = "Jefe de Infraestructura"
    AUXILIAR_INFRAESTRUCTURA = "Auxiliar de Infraestructura"
    TECNICO = "Tecnico"


class Usuario(Base):
    """
    Modelo SQLAlchemy para la tabla 'encargados'.
    Representa el personal técnico, administrativo y contratistas del sistema.

    Atributos:
        id (int): Identificador único del usuario (clave primaria).
        codigo_universitario (int): ID institucional para cruce con RRHH (único, nullable para técnicos).
        nombre (str): Primer nombre del usuario.
        apellido (str): Apellido del usuario.
        tipo_rol (str): Rol asignado ('Jefe de Infraestructura', 'Auxiliar de Infraestructura', 'Tecnico').
        telefono (str): Número de teléfono del usuario.
        correo_institucional (str): Correo institucional para notificaciones y alertas.
        hashed_password (str): Contraseña hasheada con bcrypt para autenticación.
        activo (bool): Indica si el usuario está activo o inactivo en el plantel educativo.
        created_at (datetime): Timestamp de creación del registro.
        updated_at (datetime): Timestamp de última actualización.
    """

    __tablename__ = "encargados"

    # Columnas
    id: int = Column(Integer, primary_key=True, index=True)
    codigo_universitario: Optional[int] = Column(Integer, nullable=True, unique=True, index=True)
    nombre: str = Column(String(30), nullable=False, index=True)
    apellido: str = Column(String(30), nullable=False, index=True)
    tipo_rol: str = Column(String(50), nullable=False)
    telefono: str = Column(String(12), nullable=False)
    correo_institucional: str = Column(String(50), nullable=True, unique=True, index=True)
    hashed_password: str = Column(String(255), nullable=False)
    activo: bool = Column(Boolean, default=True, nullable=False, index=True)
    created_at: datetime = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at: datetime = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Restricciones
    __table_args__ = (
        UniqueConstraint('codigo_universitario', name='uq_encargado_codigo'),
        UniqueConstraint('correo_institucional', name='uq_encargado_correo'),
        {"schema": "gestion_aires_ucc"}
    )

