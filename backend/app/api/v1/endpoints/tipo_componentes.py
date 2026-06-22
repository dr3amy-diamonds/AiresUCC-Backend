"""
Endpoints para la entidad TipoComponente.
API REST para consultar el catálogo de repuestos disponibles en el campus.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.tipo_componente import TipoComponente
from app.schemas.tipo_componente import TipoComponenteResponse
from app.schemas.mantenimiento import INSUMOS_FIJOS_TALLER

router = APIRouter(prefix="/tipo_componentes", tags=["tipo_componentes"])

@router.get("/", response_model=List[TipoComponenteResponse])
def listar_tipo_componentes(
    fijos: bool = Query(False, description="Si es true, devuelve solo los 3 insumos fijos del taller"),
    db: Session = Depends(get_db),
):
    """
    Catálogo de repuestos. Con fijos=true retorna únicamente los tres insumos
    predeterminados del formulario técnico.
    """
    try:
        query = db.query(TipoComponente)
        if fijos:
            query = query.filter(TipoComponente.nombre.in_(INSUMOS_FIJOS_TALLER))
        componentes = query.order_by(TipoComponente.id).all()
        return componentes
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al consultar el catálogo de componentes: {str(e)}"
        )