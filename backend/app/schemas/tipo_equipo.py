"""
Schemas para TipoEquipo (Pydantic models).
Validación y serialización de datos para tipos de equipos de aire acondicionado.
"""

from pydantic import BaseModel, Field
from typing import Optional


class TipoEquipoBase(BaseModel):
    """Schema base para TipoEquipo con validaciones comunes."""
    nombre: str = Field(
        ...,
        min_length=3,
        max_length=30,
        description="Nombre del tipo de equipo (ej: Mini Split, Piso Techo, Central, Ventana)"
    )


class TipoEquipoCreate(TipoEquipoBase):
    """Schema para crear un nuevo tipo de equipo."""
    pass


class TipoEquipoUpdate(BaseModel):
    """Schema para actualizar un tipo de equipo."""
    nombre: Optional[str] = Field(
        None,
        min_length=3,
        max_length=30,
        description="Nuevo nombre del tipo de equipo"
    )


class TipoEquipoResponse(TipoEquipoBase):
    """Schema para respuestas de lectura de tipo de equipo."""
    id: int = Field(..., description="ID único del tipo de equipo")

    class Config:
        from_attributes = True
