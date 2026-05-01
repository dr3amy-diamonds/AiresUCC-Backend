"""
Esquemas Pydantic para la entidad Marca.
Validación de datos para marcas de equipos de aire acondicionado.
"""

from pydantic import BaseModel, Field, ConfigDict


class MarcaBase(BaseModel):
    """Base schema para Marca."""
    nombre: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Nombre del fabricante (ej: LG, Samsung, Fujitsu)"
    )


class MarcaCreate(MarcaBase):
    """Schema para crear una nueva marca."""
    pass


class MarcaUpdate(BaseModel):
    """Schema para actualizar una marca."""
    nombre: str = Field(
        None,
        min_length=1,
        max_length=20,
        description="Nombre del fabricante"
    )


class MarcaResponse(MarcaBase):
    """Schema de respuesta para Marca."""
    id: int = Field(..., description="ID único de la marca")

    model_config = ConfigDict(from_attributes=True)

