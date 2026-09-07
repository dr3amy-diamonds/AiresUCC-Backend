"""Esquemas Pydantic para tipos de mantenimiento."""

from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class TipoMantenimientoBase(BaseModel):
    nombre: str = Field(
        ...,
        min_length=1,
        max_length=30,
        description="Nombre del tipo (ej: Preventivo, Correctivo)",
    )
    frecuencia_dias: Optional[int] = Field(
        None,
        ge=0,
        description="Días entre mantenimientos del mismo tipo (null si no aplica)",
    )


class TipoMantenimientoCreate(TipoMantenimientoBase):
    """Schema para crear un nuevo tipo de mantenimiento."""
    pass


class TipoMantenimientoUpdate(BaseModel):
    """Schema para actualizar un tipo de mantenimiento."""
    nombre: Optional[str] = Field(None, min_length=1, max_length=30)
    frecuencia_dias: Optional[int] = Field(None, ge=0)


class TipoMantenimientoResponse(TipoMantenimientoBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
