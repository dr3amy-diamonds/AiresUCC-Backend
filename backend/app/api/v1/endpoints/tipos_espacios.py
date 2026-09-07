"""Endpoints para el catálogo de tipos de espacio."""

from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.tipo_espacio import TipoEspacio
from app.schemas.tipo_espacio import TipoEspacioResponse

router = APIRouter(prefix="/tipos-espacios", tags=["tipos-espacios"])


@router.get("/", response_model=List[TipoEspacioResponse])
def listar_tipos_espacio(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Lista los tipos de espacio disponibles para formularios (Aula, Laboratorio, etc.)."""
    return db.query(TipoEspacio).order_by(TipoEspacio.id).offset(skip).limit(limit).all()
