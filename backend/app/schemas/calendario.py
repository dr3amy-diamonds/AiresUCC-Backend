"""
Esquemas Pydantic para el Resumen Anual de Calendario.

Agregación dinámica para la matriz 12x31 (/calendario):
- Un solo request reemplaza ~40 paginados (mantenimientos + programaciones + espacios).
- Celdas pre-agrupadas por (espacio_id, mes, día) vía GROUP BY en servicio.
- Eventos con detalle para el modal solo-lectura.
"""

from datetime import date
from typing import List, Optional, Union
from pydantic import BaseModel, Field, ConfigDict

from app.schemas.mantenimiento import InsumoGastadoResponse


class CalendarioEspacioItem(BaseModel):
    """Espacio canónico para filas de la matriz."""

    id: int = Field(..., description="ID del espacio (0 = Sin ubicación sintético)")
    nombre: str = Field(..., description="Nombre del espacio")
    codigo_espacio: Optional[str] = Field(None, description="Código físico en puerta")
    bloque_nombre: Optional[str] = Field(None, description="Bloque / edificio")
    piso: Optional[int] = Field(None, description="Piso")
    total: int = Field(default=0, description="Intervenciones en el año")

    model_config = ConfigDict(from_attributes=True)


class CalendarioCeldaItem(BaseModel):
    """Celda agregada: cuántas X van en (espacio, día)."""

    espacio_id: int = Field(..., description="FK a espacio (0 = sintético)")
    mes: int = Field(..., ge=1, le=12, description="Mes 1-12")
    dia: int = Field(..., ge=1, le=31, description="Día 1-31")
    conteo: int = Field(..., ge=1, description="Registros ese día")
    orden_ids: List[str] = Field(default_factory=list, description="IDs para tooltip")

    model_config = ConfigDict(from_attributes=True)


class CalendarioEventoItem(BaseModel):
    """Detalle normalizado para modal y lista móvil."""

    orden_id: str = Field(..., description="MNT-{id} u ORD-{id}")
    fecha: date = Field(..., description="Fecha YYYY-MM-DD")
    fecha_ejecucion: date = Field(..., description="Alias de fecha")
    equipo_id: Optional[int] = Field(None, description="Equipo intervenido")
    espacio_id: Optional[int] = Field(None, description="Espacio resuelto vía equipo")
    espacio_nombre: Optional[str] = Field(None, description="Nombre resuelto")
    tecnico_nombre: str = Field(default="Sin asignar")
    observaciones: Optional[str] = Field(None)
    insumos_gastados: List[InsumoGastadoResponse] = Field(default_factory=list)
    costo_total: Optional[float] = Field(None)
    estado: str = Field(default="Completado")
    origen: str = Field(default="mantenimiento", description="mantenimiento | programacion")

    model_config = ConfigDict(from_attributes=True)


class ResumenCalendarioResponse(BaseModel):
    """Respuesta única del endpoint agregado."""

    anio: int = Field(..., description="Año consultado")
    total_espacios: int = Field(..., description="Filas de la matriz")
    total_eventos: int = Field(..., description="X verdes en el año")
    espacios: List[CalendarioEspacioItem] = Field(default_factory=list)
    celdas: List[CalendarioCeldaItem] = Field(
        ..., description="Solo días con >=1 evento (GROUP BY)"
    )
    eventos: List[CalendarioEventoItem] = Field(
        ..., description="Detalle para modal / lista móvil"
    )
    por_mes: List[int] = Field(
        ..., min_length=12, max_length=12, description="Conteo ene..dic"
    )

    model_config = ConfigDict(from_attributes=True)
