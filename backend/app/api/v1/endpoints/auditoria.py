"""Endpoints REST para consulta de la bitácora de auditoría."""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.auditoria import Auditoria
from app.schemas.auditoria import AuditoriaListResponse, AuditoriaResponse
from app.core.security import require_role

router = APIRouter(prefix="/auditoria", tags=["Auditoría"])


@router.get(
    "/",
    response_model=AuditoriaListResponse,
    dependencies=[Depends(require_role(
        "Jefe de Infraestructura",
        "Auxiliar de Infraestructura",
    ))],
)
def listar_auditoria(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    tabla_afectada: Optional[str] = Query(None, description="Filtrar por tabla"),
    encargado_id: Optional[int] = Query(None, gt=0, description="Filtrar por operario"),
):
    """Consulta el historial inmutable de cambios registrados en PostgreSQL."""
    query = db.query(Auditoria)

    if tabla_afectada:
        query = query.filter(Auditoria.tabla_afectada.ilike(f"%{tabla_afectada}%"))
    if encargado_id:
        query = query.filter(Auditoria.encargado_id == encargado_id)

    total = query.count()
    registros = (
        query.order_by(Auditoria.fecha_cambio.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return AuditoriaListResponse(
        total=total,
        items=[AuditoriaResponse.model_validate(r) for r in registros],
    )
