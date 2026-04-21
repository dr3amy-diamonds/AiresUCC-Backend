"""
Modelo para la tabla de Usuarios (Encargados).
Gestión del personal técnico y administrativo que interactúa con el sistema.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, Enum, DateTime, func, UniqueConstraint
from app.db.base_class import Base
import enum


class TipoRol(str, enum.Enum):
    """Roles disponibles en el sistema."""
    ADMINISTRADOR = "Administrador"
    TECNICO = "Técnico"
    SUPERVISOR = "Supervisor"
    CONTRATISTA = "Contratista"


class Usuario(Base):
    """
    Modelo SQLAlchemy para la tabla 'usuario' (encargados).
    Representa el personal técnico, administrativo y contratistas del sistema.

    Atributos:
        id (int): Identificador único del usuario (clave primaria).
        nombre (str): Nombre del usuario.
        correo (str): Correo institucional (único). Clave para notificaciones y alertas.
        hashed_password (str): Contraseña hasheada con bcrypt.
        tipo_rol (TipoRol): Rol asignado ('Administrador', 'Técnico', 'Supervisor', 'Contratista').
        activo (bool): Indica si el usuario está activo o inactivo.
        created_at (datetime): Timestamp de creación del registro.
        updated_at (datetime): Timestamp de última actualización.
    """

    __tablename__ = "usuario"

    # Columnas
    id: int = Column(Integer, primary_key=True, index=True)
    nombre: str = Column(String(100), nullable=False, index=True)
    correo: str = Column(String(100), nullable=False, unique=True, index=True)
    hashed_password: str = Column(String(255), nullable=False)
    tipo_rol: TipoRol = Column(
        Enum(TipoRol),
        default=TipoRol.TECNICO,
        nullable=False
    )
    activo: bool = Column(Boolean, default=True, nullable=False, index=True)
    created_at: datetime = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at: datetime = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Restricciones
    __table_args__ = (
        UniqueConstraint('correo', name='uq_usuario_correo'),
    )

