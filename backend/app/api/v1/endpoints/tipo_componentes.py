"""
Endpoints para la entidad TipoComponente.
API REST para consultar el catálogo de repuestos disponibles en el campus.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.tipo_componente import TipoComponente
from app.schemas.tipo_componente import TipoComponenteResponse

router = APIRouter(prefix="/tipo_componentes", tags=["tipo_componentes"])

@router.get("/", response_model=List[TipoComponenteResponse])
def listar_tipo_componentes(db: Session = Depends(get_db)):
    """
    Obtiene la lista completa de repuestos predeterminados (Capacitor, Filtro, etc.)
    para pintar las casillas de verificación (checkboxes) en el formulario del técnico.
    """
    try:
        componentes = db.query(TipoComponente).all()
        return componentes
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al consultar el catálogo de componentes: {str(e)}"
        )