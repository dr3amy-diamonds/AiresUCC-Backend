"""Esquemas Pydantic para la entidad Auditoría."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class AuditoriaResponse(BaseModel):
    """Respuesta plana de un registro de auditoría."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    tabla_afectada: str
    registro_id: int
    campo: str
    valor_anterior: Optional[str] = None
    valor_nuevo: Optional[str] = None
    encargado_id: Optional[int] = None
    fecha_cambio: datetime


class AuditoriaListResponse(BaseModel):
    """Lista paginada de registros de auditoría."""

    total: int
    items: List[AuditoriaResponse]
