"""
Esquemas Pydantic para la entidad TipoComponente.
Validación de datos para tipos de componentes y repuestos.
"""

from pydantic import BaseModel, Field, ConfigDict


class TipoComponenteBase(BaseModel):
    """Base schema para TipoComponente."""
    nombre: str = Field(
        ...,
        min_length=1,
        max_length=60,
        description="Nombre del componente o repuesto (ej: Compresor, Filtro, Válvula)"
    )


class TipoComponenteCreate(TipoComponenteBase):
    """Schema para crear un nuevo tipo de componente."""
    pass


class TipoComponenteResponse(TipoComponenteBase):
    """Schema de respuesta para TipoComponente."""
    id: int = Field(..., description="ID único del tipo de componente")

    model_config = ConfigDict(from_attributes=True)

