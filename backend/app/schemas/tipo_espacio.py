"""Esquemas Pydantic para tipos de espacio."""

from pydantic import BaseModel, Field, ConfigDict


class TipoEspacioResponse(BaseModel):
    id: int
    nombre: str = Field(..., min_length=1, max_length=50)

    model_config = ConfigDict(from_attributes=True)
