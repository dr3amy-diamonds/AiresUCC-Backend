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
from datetime import datetime


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
    nombre: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Nombre descriptivo del bloque (ej: 'Bloque Academia', 'Bloque Administrativo')"
    )
    descripcion: Optional[str] = Field(
        None,
        max_length=500,
        description="Descripción general del bloque y su ubicación"
    )


class BloqueCreate(BloqueBase):
    """
    Esquema para creación de nuevo bloque.

    Validación Pydantic:
    - Código único a nivel global
    - Nombre descriptivo y único
    - Descripción opcional para documentación
    """
    pass


class BloqueUpdate(BaseModel):
    """
    Esquema para actualizar un bloque existente.

    IMPORTANTE:
    - NO se puede cambiar codigo_bloque (auditoría)
    - Solo se puede cambiar: nombre, descripción
    """
    nombre: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Actualizar nombre del bloque"
    )
    descripcion: Optional[str] = Field(
        None,
        max_length=500,
        description="Actualizar descripción del bloque"
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
    - Nombre y descripción completa
    """
    id: int = Field(..., description="Identificador único del bloque")
    codigo_bloque: str

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


"""
NOTAS DE IMPLEMENTACIÓN:

1. ORGANIZACIÓN FÍSICA:
   Campus Montería
   ├── Bloque A (Academia)
   │   ├── Espacio A-101 (Aula)
   │   ├── Espacio A-102 (Laboratorio)
   │   └── Espacio A-201 (Oficina)
   ├── Bloque B (Administrativo)
   ├── Bloque C (Biblioteca)
   └── ...

2. BÚSQUEDAS COMUNES:
   - GET /bloques                  → Todos los bloques
   - GET /bloques/{id}             → Detalles de un bloque
   - GET /bloques/{id}/estadisticas → KPIs por bloque

3. DASHBOARDS:
   - Mapa de bloques con indicador de salud
   - Resumen de disponibilidad por bloque
   - Alertas críticas agrupadas por bloque

4. PAGINACIÓN RECOMENDADA:
   - limit=20 (cantidad de bloques típicamente pequeña)
   - Todos los bloques podrían caber en una sola página
"""

