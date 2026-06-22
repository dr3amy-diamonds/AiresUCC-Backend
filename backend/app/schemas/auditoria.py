"""
Esquemas Pydantic para Auditoría de Negocio (Bitácora de Eventos).

Regla de negocio: la validación ocurre aquí antes de cualquier persistencia,
impidiendo cancelaciones sin motivo explicado.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ============================================================================
# ENUMS DE DOMINIO
# ============================================================================

class TipoActorEnum(str, Enum):
    """Clasificación narrativa del actor que ejecutó el evento."""
    SUPER_USUARIO = "super_usuario"
    TECNICO = "tecnico"
    DESCONOCIDO = "desconocido"


class CategoriaEventoEnum(str, Enum):
    """Categorías de negocio persistidas en auditoria.tipo_evento."""
    PROGRAMACION_MANTENIMIENTO = "Programación de mantenimiento"
    CRUD_EQUIPOS = "CRUD de equipos"
    CRUD_USUARIOS = "CRUD de usuarios"
    CRUD_TIPOS_EQUIPO = "CRUD de tipos de equipo"
    CRUD_TIPOS_MANTENIMIENTO = "CRUD de tipos de mantenimiento"
    CAMBIO_PERMISOS = "Cambio de permisos"


# Alias internos → categoría de negocio (compatibilidad con eventos legacy)
class TipoEventoEnum(str, Enum):
    """Tipos de evento reconocidos por la bitácora de gestión."""
    PROGRAMACION_MANTENIMIENTO = CategoriaEventoEnum.PROGRAMACION_MANTENIMIENTO.value
    CRUD_EQUIPOS = CategoriaEventoEnum.CRUD_EQUIPOS.value
    CRUD_USUARIOS = CategoriaEventoEnum.CRUD_USUARIOS.value
    CRUD_TIPOS_EQUIPO = CategoriaEventoEnum.CRUD_TIPOS_EQUIPO.value
    CRUD_TIPOS_MANTENIMIENTO = CategoriaEventoEnum.CRUD_TIPOS_MANTENIMIENTO.value
    CAMBIO_PERMISOS = CategoriaEventoEnum.CAMBIO_PERMISOS.value
    # Legacy (mapeados en presentación)
    CIERRE_ORDEN = "cierre_orden"
    CANCELACION = "cancelacion"
    CAMBIO_ESTADO = "cambio_estado"
    CREACION = "creacion"
    REGISTRO_TECNICO = "registro_tecnico"
    LEGACY = "legacy"


ESTADOS_CANCELACION = frozenset({
    "cancelado",
    "Cancelado",
    "CANCELADO",
})

JUSTIFICACION_MIN_CARACTERES = 20


# ============================================================================
# ENTRADA — EVENT PROCESSOR
# ============================================================================

class EventoAuditoriaCreate(BaseModel):
    """
    Contrato de entrada para el Event Processor.

    Regla de negocio: si el estado destino implica cancelación,
    la justificación es obligatoria y debe ser sustantiva.
    """

    tipo_evento: TipoEventoEnum
    encargado_id: int = Field(..., gt=0, description="ID del usuario que ejecuta la acción")
    registro_id: int = Field(..., gt=0, description="ID del registro de negocio afectado")
    tabla_afectada: str = Field(..., min_length=2, max_length=60)
    campo: Optional[str] = Field(None, max_length=60, description="Campo técnico afectado")

    estado_anterior: Optional[str] = Field(None, max_length=60)
    estado_nuevo: Optional[str] = Field(None, max_length=60)
    justificacion: Optional[str] = Field(None, max_length=500)

    equipo_id: Optional[int] = Field(None, gt=0, description="Para resolver ubicación y recurso")
    recurso_descripcion: Optional[str] = Field(None, max_length=200)
    ubicacion_snapshot: Optional[str] = Field(
        None,
        description="Texto plano capturado en el instante del evento (Snapshot Policy)",
    )
    detalle_operativo: Optional[str] = Field(
        None,
        max_length=1000,
        description="Resumen del reporte técnico u observación operativa",
    )
    mantenimiento_id: Optional[int] = Field(None, gt=0)

    model_config = ConfigDict(extra="forbid")

    @field_validator("justificacion")
    @classmethod
    def normalizar_justificacion(cls, valor: Optional[str]) -> Optional[str]:
        if valor is None:
            return None
        return valor.strip()

    @model_validator(mode="after")
    def exigir_justificacion_en_cancelacion(self) -> "EventoAuditoriaCreate":
        """
        Regla de negocio: ninguna cancelación puede persistirse sin motivo documentado.
        """
        implica_cancelacion = (
            self.tipo_evento == TipoEventoEnum.CANCELACION
            or (self.campo or "").strip().lower() == "cancelacion"
            or (self.estado_nuevo or "").strip() in ESTADOS_CANCELACION
        )

        if not implica_cancelacion:
            return self

        texto = (self.justificacion or "").strip()
        if len(texto) < JUSTIFICACION_MIN_CARACTERES:
            raise ValueError(
                f"Las cancelaciones requieren una justificación de al menos "
                f"{JUSTIFICACION_MIN_CARACTERES} caracteres."
            )
        return self


class CancelacionProgramacionRequest(BaseModel):
    """
    Solicitud de cancelación administrativa con motivo obligatorio.

    Regla de negocio: el motivo se valida antes de tocar la base de datos.
    """

    justificacion: str = Field(
        ...,
        min_length=JUSTIFICACION_MIN_CARACTERES,
        max_length=500,
        description="Motivo documentado de la cancelación",
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("justificacion")
    @classmethod
    def justificacion_no_vacia(cls, valor: str) -> str:
        texto = valor.strip()
        if len(texto) < JUSTIFICACION_MIN_CARACTERES:
            raise ValueError(
                f"La justificación debe tener al menos {JUSTIFICACION_MIN_CARACTERES} caracteres."
            )
        return texto


# ============================================================================
# METADATOS INTERNOS — NARRADOR
# ============================================================================

class EventoNarrativaMetadatos(BaseModel):
    """Metadatos ya resueltos (nombres, no IDs) para audit_narrator."""

    tipo_actor: TipoActorEnum
    tipo_evento: TipoEventoEnum
    actor_nombre: str
    actor_rol_etiqueta: str
    recurso_descripcion: str
    ubicacion_snapshot: str
    estado_anterior: Optional[str] = None
    estado_nuevo: Optional[str] = None
    justificacion: Optional[str] = None
    detalle_operativo: Optional[str] = None
    tabla_tecnica: Optional[str] = None
    campo_tecnico: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


# ============================================================================
# SALIDA — CAPA DE PRESENTACIÓN (FRONTEND)
# ============================================================================

class EventoGestionPresentacion(BaseModel):
    """
    DTO listo para renderizar: el frontend no interpreta ni transforma.

    Regla de negocio: fecha, rol, ubicación y narrativa llegan resueltos desde el backend.
    """

    id: int
    fecha_hora: str = Field(..., description="Fecha y hora pre-formateada para la UI")
    actor_nombre: str
    actor_rol_etiqueta: str
    ubicacion: str
    narrativa: str
    tipo_evento_etiqueta: str

    model_config = ConfigDict(from_attributes=False)


class BitacoraListResponse(BaseModel):
    """Respuesta paginada de la bitácora de gestión."""

    total: int
    items: List[EventoGestionPresentacion]


# ============================================================================
# COMPATIBILIDAD — RESPUESTA TÉCNICA LEGACY
# ============================================================================

class AuditoriaResponse(BaseModel):
    """Respuesta plana legacy (solo consultas internas o migración)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    tabla_afectada: str
    registro_id: int
    campo: str
    valor_anterior: Optional[str] = None
    valor_nuevo: Optional[str] = None
    encargado_id: Optional[int] = None
    fecha_cambio: datetime
    narrativa: Optional[str] = None


class AuditoriaListResponse(BaseModel):
    """Lista paginada legacy."""

    total: int
    items: List[AuditoriaResponse]
