"""
Esquemas Pydantic para la entidad Espacio.

Este módulo define los contratos de validación para:
- Creación de espacios (ubicaciones físicas)
- Actualización de datos de espacios
- Respuestas con información de localización
- Relaciones con bloques y tipos de espacios

Arquitectura:
- Validación estricta de códigos únicos
- Jerarquía: Bloque → Espacio → Equipos
- Piso para visualización vertical en mapas
- Documentación completa con ejemplos
"""

import re
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from datetime import datetime


PISO_MIN = 1
PISO_MAX = 7


def _primer_digito(texto: Optional[str]) -> Optional[int]:
    if not texto:
        return None
    m = re.search(r"\d", texto.strip())
    return int(m.group(0)) if m else None


def validar_coherencia_aula_piso(nombre: Optional[str], codigo: Optional[str], piso: Optional[int]) -> None:
    if piso is None:
        return
    for etiqueta in (nombre, codigo):
        digito = _primer_digito(etiqueta)
        if digito is not None and digito != int(piso):
            raise ValueError(
                f"Incoherencia aula/piso: '{etiqueta}' inicia en {digito} pero piso={piso}"
            )


# ============================================================================
# ESQUEMAS BASE Y CREATE
# ============================================================================

class EspacioBase(BaseModel):
    """Esquema base con campos comunes de espacio."""
    codigo_espacio: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Código físico único en la puerta del salón (ej: 'A-204')"
    )
    nombre: str = Field(
        ...,
        min_length=1,
        max_length=65,
        description="Nombre del espacio (ej: 'Aula 204', 'Laboratorio 1')"
    )
    piso: Optional[int] = Field(
        None,
        ge=PISO_MIN,
        le=PISO_MAX,
        description="Número de piso para visualización (1-7: pisos superiores)"
    )

    @model_validator(mode="after")
    def _coherencia_aula_piso(self):
        validar_coherencia_aula_piso(self.nombre, self.codigo_espacio, self.piso)
        return self
    bloque_id: int = Field(
        ...,
        gt=0,
        description="ID del bloque al que pertenece este espacio"
    )
    tipo_espacio_id: int = Field(
        ...,
        gt=0,
        description="ID del tipo de espacio (Aula, Oficina, Laboratorio, etc)"
    )


class EspacioCreate(BaseModel):
    """
    Esquema para creación de nuevo espacio.

    tipo_espacio_id es opcional: el modal rápido de gestión no lo envía;
    el backend asigna un tipo por defecto del catálogo cuando falta.
    """
    codigo_espacio: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Código físico único en la puerta del salón (ej: 'A-204')"
    )
    nombre: str = Field(
        ...,
        min_length=1,
        max_length=65,
        description="Nombre del espacio (ej: 'Aula 204', 'Laboratorio 1')"
    )
    piso: Optional[int] = Field(
        None,
        ge=PISO_MIN,
        le=PISO_MAX,
        description="Número de piso para visualización (1-7: pisos superiores)"
    )
    bloque_id: int = Field(
        ...,
        gt=0,
        description="ID del bloque al que pertenece este espacio"
    )

    tipo_espacio_id: Optional[int] = Field(
        None,
        gt=0,
        description="ID del tipo de espacio. Opcional; si no se envía, se usa uno por defecto."
    )

    @model_validator(mode="after")
    def _coherencia_aula_piso_create(self):
        validar_coherencia_aula_piso(self.nombre, self.codigo_espacio, self.piso)
        return self


class EspacioUpdate(BaseModel):
    """
    Esquema para actualizar un espacio existente.

    IMPORTANTE:
    - NO se puede cambiar bloque_id (violaría integridad física)
    - Se puede corregir: codigo_espacio, nombre, piso, tipo_espacio_id
    """
    codigo_espacio: Optional[str] = Field(
        None,
        min_length=1,
        max_length=20,
        description="Corregir código del espacio"
    )
    nombre: Optional[str] = Field(
        None,
        min_length=1,
        max_length=65,
        description="Actualizar nombre del espacio"
    )
    piso: Optional[int] = Field(
        None,
        ge=PISO_MIN,
        le=PISO_MAX,
        description="Actualizar número de piso (1-7)"
    )
    tipo_espacio_id: Optional[int] = Field(
        None,
        gt=0,
        description="Cambiar tipo de espacio"
    )

    @model_validator(mode="after")
    def _coherencia_aula_piso_update(self):
        validar_coherencia_aula_piso(self.nombre, self.codigo_espacio, self.piso)
        return self

    model_config = ConfigDict(extra="forbid")


# ============================================================================
# ESQUEMAS DE RESPUESTA
# ============================================================================

class BloqueResumenEspacio(BaseModel):
    """Mini-esquema para bloque en respuesta de espacio."""
    id: int
    codigo_bloque: str
    nombre_bloque: str

    model_config = ConfigDict(from_attributes=True)


class TipoEspacioResumen(BaseModel):
    """Mini-esquema para tipo de espacio en respuesta."""
    id: int
    nombre: str

    model_config = ConfigDict(from_attributes=True)


class EspacioResponse(EspacioBase):
    """
    Esquema para devolver datos de espacio de forma segura.

    Auditoría:
    - ID único para rastreabilidad
    - Código espacial para búsquedas rápidas
    - Nombre descriptivo
    - Relaciones anidadas opcionales (bloque, tipo)
    """
    id: int = Field(..., description="Identificador único del espacio")
    bloque: Optional[BloqueResumenEspacio] = Field(None, description="Información del bloque relacionado")
    tipo_espacio: Optional[TipoEspacioResumen] = Field(None, description="Información del tipo de espacio")

    model_config = ConfigDict(from_attributes=True)


class EspacioListResponse(BaseModel):
    """Respuesta paginada de espacios."""
    total: int = Field(..., description="Total de espacios")
    page: int = Field(..., description="Número de página")
    size: int = Field(..., description="Registros por página")
    items: list[EspacioResponse] = Field(..., description="Lista de espacios")


class EspacioDetalladoResponse(EspacioResponse):
    """
    Respuesta extendida de espacio con equipos instalados.

    Útil para consultar qué aires hay en un espacio específico.
    """
    cantidad_equipos: int = Field(..., description="Total de equipos instalados")
    equipos_operativos: int = Field(..., description="Equipos en estado operativo")
    equipos_fuera_servicio: int = Field(..., description="Equipos en mantenimiento o fuera de uso")


class EspacioResumenPorBloque(BaseModel):
    """
    Esquema para resumir espacios por bloque.

    Useful para dashboards: {bloque: {espacios: [...]}}
    """
    bloque_id: int
    bloque_nombre: str
    total_espacios: int
    espacios: list[EspacioResponse]


"""
NOTAS DE IMPLEMENTACIÓN:

1. JERARQUÍA FÍSICA:
   Campus → Bloque → Espacio → Equipos
   
2. BÚSQUEDAS COMUNES:
   - GET /espacios?bloque_id=1          → Todos los espacios del bloque A
   - GET /espacios?tipo_espacio_id=2    → Todos los laboratorios
   - GET /espacios?codigo_espacio=A-204 → Búsqueda por código

3. VISUALIZACIÓN EN MAPAS:
   - Usar piso para agrupar por nivel vertical
   - codigo_espacio como etiqueta en plano
   - nombre como tooltip

4. EQUIPOS POR ESPACIO:
   - Relación: Espacio → múltiples Equipos
   - Dashboard muestra capacidad BTU total por espacio
   - Alerta si sin refrigeración en espacio crítico
"""

