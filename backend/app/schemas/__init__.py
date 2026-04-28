"""
Esquemas Pydantic para validación de datos.

Exporta todos los modelos de validación para fácil importación:
from app.schemas import UsuarioCreate, UsuarioResponse, Token, etc.
"""

# Esquemas de Usuario
from .usuario import (
    UsuarioBase,
    UsuarioCreate,
    UsuarioResponse,
    UsuarioResponseAdmin,
    UsuarioUpdate,
    UsuarioChangePassword,
    UsuarioLogin,
    Token,
    TokenData,
    UsuarioListResponse,
    TipoRolSchema,
)

# Esquemas de Equipo
from .equipo import EquipoBase, EquipoCreate, EquipoResponse

__all__ = [
    # Usuario
    "UsuarioBase",
    "UsuarioCreate",
    "UsuarioResponse",
    "UsuarioResponseAdmin",
    "UsuarioUpdate",
    "UsuarioChangePassword",
    "UsuarioLogin",
    "Token",
    "TokenData",
    "UsuarioListResponse",
    "TipoRolSchema",
    # Equipo
    "EquipoBase",
    "EquipoCreate",
    "EquipoResponse",
]

