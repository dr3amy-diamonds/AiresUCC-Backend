"""
Módulo de componentes centrales de la aplicación.
Incluye seguridad, configuración y funciones de utilidad.
"""

from app.core.security import (
    hashear_contrasena,
    verificar_contrasena,
    crear_token_acceso,
    verificar_token,
    require_role,
    get_current_user,
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

__all__ = [
    "hashear_contrasena",
    "verificar_contrasena",
    "crear_token_acceso",
    "verificar_token",
    "require_role",
    "get_current_user",
    "SECRET_KEY",
    "ALGORITHM",
    "ACCESS_TOKEN_EXPIRE_MINUTES",
]
