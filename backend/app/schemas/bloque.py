"""
Esquemas Pydantic para la entidad Bloque.

Este módulo define los contratos de validación para:
- Creación de bloques (estructuras físicas de la UCC)
- Actualización de datos de bloques
- Respuestas con información de bloques
- Listados y búsquedas

Arquitectura:
- Bloque es la unidad superior de organización física
- Contiene múltiples espacios (aulas, laboratorios, oficinas)
- Validación estricta de códigos únicos
- Documentación completa
"""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# ESQUEMAS BASE Y CREATE
# ============================================================================

class BloqueBase(BaseModel):
    """Esquema base con campos comunes de bloque."""
    codigo_bloque: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Código único del bloque (ej: 'BLOQUE-A', 'BLOQUE-1')"
    )
    nombre_bloque: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Nombre descriptivo del bloque (ej: 'Bloque Academia', 'Bloque Administrativo')"
    )


class BloqueCreate(BloqueBase):
    """
    Esquema para creación de nuevo bloque.

    Validación Pydantic:
    - Código único a nivel global
    - Nombre descriptivo y único
    """
    pass


class BloqueUpdate(BaseModel):
    """
    Esquema para actualizar un bloque existente.

    IMPORTANTE:
    - NO se puede cambiar codigo_bloque (auditoría)
    - Solo se puede cambiar: nombre_bloque
    """
    nombre_bloque: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Actualizar nombre del bloque"
    )

    model_config = ConfigDict(extra="forbid")


# ============================================================================
# ESQUEMAS DE RESPUESTA
# ============================================================================

class BloqueResponse(BloqueBase):
    """
    Esquema para devolver datos de bloque de forma segura.

    Auditoría:
    - ID único para rastreabilidad
    - Código espacial para referencias físicas
    - Nombre descriptivo
    """
    id: int = Field(..., description="Identificador único del bloque")

    model_config = ConfigDict(from_attributes=True)


class BloqueListResponse(BaseModel):
    """Respuesta paginada de bloques."""
    total: int = Field(..., description="Total de bloques")
    page: int = Field(..., description="Número de página")
    size: int = Field(..., description="Registros por página")
    items: list[BloqueResponse] = Field(..., description="Lista de bloques")


class BloqueDetalladoResponse(BloqueResponse):
    """
    Respuesta extendida de bloque con estadísticas.

    Útil para dashboards administrativos.
    """
    total_espacios: int = Field(..., description="Cantidad de espacios en el bloque")
    total_equipos: int = Field(..., description="Cantidad de equipos instalados en el bloque")
    equipos_operativos: int = Field(..., description="Equipos en funcionamiento")
    equipos_fuera_servicio: int = Field(..., description="Equipos en mantenimiento o inactivos")
    capacidad_btu_total: int = Field(..., description="Capacidad BTU total instalada")


class BloqueResumenAnalytica(BaseModel):
    """
    Esquema para resumen de bloque en dashboards analíticos.
    """
    bloque_id: int
    bloque_nombre: str
    espacios_count: int
    equipos_count: int
    equipos_operativos: int
    porcentaje_disponibilidad: float
    btu_total: int



