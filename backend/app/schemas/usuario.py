"""
Esquemas Pydantic para la entidad Usuario (tabla: encargados).

Este módulo define los contratos de validación de datos para:
- Registro e ingreso de usuarios (encargados)
- Respuestas seguras (sin exponer hashed_password)
- Autenticación y tokens
- Sincronización exacta con tabla encargados de BD

Campos mapeados a tabla:
- usuario.id → encargados.id
- usuario.nombre → encargados.nombre
- usuario.apellido → encargados.apellido
- usuario.correo_institucional → encargados.correo_institucional
- usuario.hashed_password → encargados.hashed_password
- usuario.codigo_universitario → encargados.codigo_universitario
- usuario.telefono → encargados.telefono
- usuario.tipo_rol → encargados.tipo_rol
- usuario.activo → encargados.activo
- usuario.created_at → encargados.created_at
- usuario.updated_at → encargados.updated_at
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from enum import Enum


# ============================================================================
# ENUMS Y CONSTANTES
# ============================================================================

class TipoRolSchema(str, Enum):
    """
    Roles disponibles en el sistema.

    Solo 3 roles permitidos, mapeados a la tabla encargados:
    - Jefe de Infraestructura: Máximos privilegios (equivalente a Admin)
    - Auxiliar de Infraestructura: Privilegios limitados
    - Tecnico: Técnico operativo
    """
    JEFE_INFRAESTRUCTURA = "Jefe de Infraestructura"
    AUXILIAR_INFRAESTRUCTURA = "Auxiliar de Infraestructura"
    TECNICO = "Tecnico"


# ============================================================================
# ESQUEMAS BASE Y CREATE
# ============================================================================

class UsuarioBase(BaseModel):
    """
    Esquema base con campos comunes a múltiples contextos.

    Contiene los atributos esenciales del usuario que son compartidos
    entre creación y respuesta (excepto hashed_password que nunca sale).

    Mapeado con tabla encargados:
    - nombre: primer nombre
    - apellido: apellido del usuario
    - correo_institucional: correo único (NO correo)
    - telefono: número de contacto
    - codigo_universitario: ID institucional (opcional en algunos contextos)
    - tipo_rol: solo los 3 roles permitidos
    - activo: estado del usuario
    """
    nombre: str = Field(
        ...,
        min_length=1,
        max_length=30,
        description="Primer nombre del usuario (1-30 caracteres)"
    )
    apellido: str = Field(
        ...,
        min_length=1,
        max_length=30,
        description="Apellido del usuario (1-30 caracteres)"
    )
    correo_institucional: EmailStr = Field(
        ...,
        description="Correo institucional único (NO correo simple). Validado con EmailStr."
    )
    telefono: str = Field(
        ...,
        min_length=7,
        max_length=12,
        description="Teléfono de contacto del usuario (formato: 7-12 caracteres)"
    )
    codigo_universitario: Optional[int] = Field(
        default=None,
        description="Código universitario/ID institucional numérico (opcional, debe ser único si se proporciona)"
    )
    tipo_rol: TipoRolSchema = Field(
        default=TipoRolSchema.TECNICO,
        description="Rol asignado: Jefe de Infraestructura (Admin), Auxiliar o Tecnico"
    )
    activo: bool = Field(
        default=True,
        description="Indica si el usuario está activo (True) o inactivo (False)"
    )


class UsuarioCreate(UsuarioBase):
    """
    Esquema para la creación de nuevos usuarios (encargados).

    Hereda de UsuarioBase y agrega el campo 'password' (en texto plano).
    ¡CRÍTICO! Este campo JAMÁS debe salir del backend sin ser hasheado.
    La contraseña se hashea inmediatamente en la capa de servicios.

    Validación Pydantic:
    - Previene que un cliente envíe hashed_password directamente
    - Valida formato de email antes de llegar a la BD
    - Asegura que rol sea uno de los 3 valores permitidos (Enum)
    - Valida que correo_institucional (NO correo) sea proporcionado
    """
    password: str = Field(
        ...,
        min_length=8,
        max_length=255,
        description="Contraseña en texto plano (8-255 caracteres). Será hasheada con bcrypt en el backend"
    )


# ============================================================================
# ESQUEMAS DE RESPUESTA (SEGUROS)
# ============================================================================

class UsuarioResponse(BaseModel):
    """
    Esquema para devolver datos de usuario de forma segura.

    SEGURIDAD CRÍTICA:
    - from_attributes=True: Permite crear el modelo desde un objeto SQLAlchemy
    - NO incluye 'password' ni 'hashed_password' en la respuesta
    - Solo devuelve campos "públicos" que pueden mostrarse al cliente
    - Mapeado exactamente con campos de tabla encargados

    Pydantic previene accidentalmente exponer secrets al:
    - Usar este esquema como "contrato" de salida
    - Rechazar campos no definidos si están marcados como exclusivos
    - Permitir que solo estos campos específicos salgan del backend
    """
    id: int = Field(..., description="Identificador único del usuario")
    nombre: str = Field(..., description="Primer nombre del usuario")
    apellido: str = Field(..., description="Apellido del usuario")
    correo_institucional: EmailStr = Field(..., description="Correo institucional (NO correo)")
    telefono: str = Field(..., description="Teléfono de contacto")
    codigo_universitario: Optional[int] = Field(None, description="Código universitario/ID institucional numérico")
    tipo_rol: TipoRolSchema = Field(..., description="Rol asignado")
    activo: bool = Field(..., description="Estado del usuario (activo/inactivo)")
    created_at: datetime = Field(..., description="Timestamp de creación del registro")
    updated_at: datetime = Field(..., description="Timestamp de última actualización")

    model_config = ConfigDict(from_attributes=True)


class UsuarioResponseAdmin(UsuarioResponse):
    """
    Esquema extendido para administradores (opcional para auditoría interna).

    Incluye timestamps sin exponer la contraseña.
    Útil para logs de auditoría y gestión de usuarios.
    """
    pass


# ============================================================================
# ESQUEMAS DE AUTENTICACIÓN
# ============================================================================

class Token(BaseModel):
    """
    Respuesta al endpoint de login.

    Contiene:
    - access_token: JWT firmado con la identidad del usuario
    - token_type: Tipo de token (siempre "bearer" para OAuth2)
    """
    access_token: str = Field(
        ...,
        description="Token JWT firmado con la información del usuario"
    )
    token_type: str = Field(
        default="bearer",
        description="Tipo de token autenticación (OAuth2)"
    )


class TokenData(BaseModel):
    """
    Payload decodificado de un JWT.

    Se extrae del token para validar quién hace la petición.
    Contiene los datos mínimos necesarios para autorización.

    DISEÑO:
    - correo_institucional como identificador único (no ID, ya que email es único)
    - Rol para control de acceso basado en roles (RBAC)
    - Estos datos NO se modifican sin revalidación
    """
    correo_institucional: EmailStr = Field(
        ...,
        description="Correo institucional del usuario autenticado (del JWT)"
    )
    tipo_rol: TipoRolSchema = Field(
        ...,
        description="Rol del usuario para autorización en endpoints"
    )


class UsuarioLogin(BaseModel):
    """
    Esquema para el login (credenciales).

    Validación:
    - correo_institucional validado con EmailStr (previene inyecciones)
    - Password es string, se comparará con hash en BD
    - Debe usarse correo_institucional (NO correo simple)
    """
    correo_institucional: EmailStr = Field(
        ...,
        description="Correo institucional del usuario (NO correo simple)"
    )
    password: str = Field(
        ...,
        description="Contraseña en texto plano (se compara con el hash)"
    )


# ============================================================================
# ESQUEMAS PARA OPERACIONES ADICIONALES
# ============================================================================

class UsuarioUpdate(BaseModel):
    """
    Esquema para actualizar un usuario existente.

    IMPORTANTE:
    - Todos los campos son opcionales (Optional)
    - NO incluye password (se actualiza en endpoint separado)
    - Permite actualizar: nombre, apellido, telefono, tipo_rol, activo
    - NO permite cambiar correo_institucional directamente (por auditoría)
    - Pydantic valida que solo estos campos permitidos se actualicen
    """
    nombre: Optional[str] = Field(
        None,
        min_length=1,
        max_length=30,
        description="Nuevo nombre (opcional)"
    )
    apellido: Optional[str] = Field(
        None,
        min_length=1,
        max_length=30,
        description="Nuevo apellido (opcional)"
    )
    telefono: Optional[str] = Field(
        None,
        min_length=7,
        max_length=12,
        description="Nuevo teléfono (opcional)"
    )
    tipo_rol: Optional[TipoRolSchema] = Field(
        None,
        description="Nuevo rol (opcional)"
    )
    activo: Optional[bool] = Field(
        None,
        description="Activar/desactivar usuario (opcional)"
    )

    model_config = ConfigDict(extra="forbid")  # Rechaza campos no definidos


class UsuarioChangePassword(BaseModel):
    """
    Esquema para cambiar contraseña (endpoint separado y seguro).

    Validación:
    - Requiere contraseña actual (para verificación)
    - Nueva contraseña con mínimo de caracteres
    - Pydantic valida formatos antes de que lleguen a servicios
    """
    current_password: str = Field(
        ...,
        description="Contraseña actual para verificación"
    )
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=255,
        description="Nueva contraseña (8-255 caracteres)"
    )


# ============================================================================
# ESQUEMAS DE PAGINACIÓN (PARA LISTADOS)
# ============================================================================

class UsuarioListResponse(BaseModel):
    """
    Respuesta paginada de usuarios (para GET /usuarios/).

    Contiene múltiples usuarios con metadatos de paginación.
    """
    total: int = Field(..., description="Total de usuarios en la BD")
    page: int = Field(..., description="Número de página actual")
    size: int = Field(..., description="Cantidad de registros por página")
    items: list[UsuarioResponse] = Field(..., description="Lista de usuarios en esta página")

