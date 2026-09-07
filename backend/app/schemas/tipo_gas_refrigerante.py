"""Esquemas Pydantic para tipos de gas refrigerante."""

from pydantic import BaseModel, Field, ConfigDict


class TipoGasRefrigeranteBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=20, description="Nombre del refrigerante (ej: R410A)")


class TipoGasRefrigeranteCreate(TipoGasRefrigeranteBase):
    pass


class TipoGasRefrigeranteUpdate(BaseModel):
    nombre: str = Field(None, min_length=1, max_length=20)


class TipoGasRefrigeranteResponse(TipoGasRefrigeranteBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
