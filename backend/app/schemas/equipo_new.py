"""
Esquemas Pydantic para la entidad Equipo.
Validación de datos para equipos de aire acondicionado.
"""

from datetime import date
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class EquipoBase(BaseModel):
    """Base schema para Equipo."""
    codigo_activo: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Plaqueta de inventario oficial de la UCC"
    )
    modelo: Optional[str] = Field(
        None,
        max_length=50,
        description="Modelo del equipo (ej: LG AS-W12GQLDG0)"
    )
    capacidad_btu: int = Field(
        ...,
        gt=0,
        description="Capacidad en BTU del equipo"
    )
    fecha_instalacion: Optional[date] = Field(
        None,
        description="Fecha de instalación del equipo"
    )
    estado: str = Field(
        default="Operativo",
        description="Estado del equipo (Operativo, En reparacion, Inactivo, Dado de baja)"
    )
    marca_id: int = Field(..., description="ID de la marca del equipo")
    tipo_equipo_id: int = Field(..., description="ID del tipo de equipo")
    espacio_id: int = Field(..., description="ID del espacio donde está instalado")


class EquipoCreate(EquipoBase):
    """Schema para crear un nuevo equipo."""
    pass


class EquipoUpdate(BaseModel):
    """Schema para actualizar un equipo."""
    modelo: Optional[str] = None
    capacidad_btu: Optional[int] = None
    fecha_instalacion: Optional[date] = None
    estado: Optional[str] = None
    espacio_id: Optional[int] = None


class EquipoResponse(EquipoBase):
    """Schema de respuesta para Equipo."""
    id: int = Field(..., description="ID único del equipo")

    model_config = ConfigDict(from_attributes=True)


class EquipoListResponse(BaseModel):
    """Response paginada de equipos."""
    total: int = Field(..., description="Total de equipos")
    page: int = Field(..., description="Número de página")
    size: int = Field(..., description="Cantidad por página")
    items: list[EquipoResponse] = Field(..., description="Lista de equipos")

