"""
Módulo de servicios para el sistema de gestión de aires acondicionados.
Contiene lógica de negocio, análisis de datos y operaciones auxiliares.
"""

from app.services.analytics import MaintenanceAnalytics, ResumenAnalytica
from app.services.usuario import (
    obtener_usuario_por_id,
    obtener_usuario_por_email,
    obtener_usuarios,
    crear_usuario,
    actualizar_usuario,
    usuario_existe,
    obtener_usuarios_activos,
    obtener_usuarios_por_rol,
)

__all__ = [
    # Analytics
    "MaintenanceAnalytics",
    "ResumenAnalytica",
    # Usuario
    "obtener_usuario_por_id",
    "obtener_usuario_por_email",
    "obtener_usuarios",
    "crear_usuario",
    "actualizar_usuario",
    "usuario_existe",
    "obtener_usuarios_activos",
    "obtener_usuarios_por_rol",
]

