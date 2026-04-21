from pydantic import BaseModel
from typing import Optional
from datetime import date

class EquipoBase(BaseModel):
    serial: str
    modelo: str

class EquipoCreate(EquipoBase):
    pass

class EquipoResponse(EquipoBase):
    id: int

    class Config:
        from_attributes = True