"""
Módulo de modelos SQLAlchemy para el sistema de gestión de aires acondicionados.
Centraliza las importaciones de los modelos para facilitar su uso en toda la aplicación.
"""

from app.models.marca import Marca
from app.models.equipo import Equipo, EstadoEquipo
from app.models.usuario import Usuario, TipoRol

__all__ = [
    "Marca",
    "Equipo",
    "EstadoEquipo",
    "Usuario",
    "TipoRol",
]
