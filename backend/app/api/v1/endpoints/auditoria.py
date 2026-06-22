"""Endpoints REST para la Bitácora de Eventos de Gestión."""

from datetime import date, datetime, time
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import distinct

from app.db.session import get_db
from app.models.auditoria import Auditoria
from app.models.espacio import Espacio
from app.models.bloque import Bloque
from app.schemas.auditoria import BitacoraListResponse
from app.core.security import require_role
from app.services.audit_presentacion import a_evento_presentacion

router = APIRouter(prefix="/auditoria", tags=["Auditoría"])


def _aplicar_filtro_ubicacion(query, db: Session, bloque_id, piso, espacio_id):
    """Filtra por jerarquía bloque → piso → espacio usando el snapshot de texto."""
    if espacio_id:
        espacio = db.query(Espacio).filter(Espacio.id == espacio_id).first()
        if espacio:
            if espacio.nombre:
                query = query.filter(Auditoria.ubicacion_snapshot.ilike(f"%{espacio.nombre}%"))
            if espacio.piso is not None:
                query = query.filter(Auditoria.ubicacion_snapshot.ilike(f"%Piso {espacio.piso}%"))
        return query

    if piso is not None:
        query = query.filter(Auditoria.ubicacion_snapshot.ilike(f"%Piso {piso}%"))

    if bloque_id:
        bloque = db.query(Bloque).filter(Bloque.id == bloque_id).first()
        if bloque and bloque.nombre_bloque:
            query = query.filter(Auditoria.ubicacion_snapshot.ilike(f"%{bloque.nombre_bloque}%"))

    return query


@router.get(
    "/tipos-evento",
    response_model=List[str],
    summary="Categorías distintas de eventos en la bitácora",
    dependencies=[Depends(require_role(
        "Jefe de Infraestructura",
        "Auxiliar de Infraestructura",
    ))],
)
def listar_tipos_evento_bitacora(db: Session = Depends(get_db)):
    """Devuelve los valores distintos de tipo_evento existentes en auditoría."""
    filas = (
        db.query(distinct(Auditoria.tipo_evento))
        .filter(Auditoria.tipo_evento.isnot(None))
        .order_by(Auditoria.tipo_evento)
        .all()
    )
    return [f[0] for f in filas if f[0]]


@router.get(
    "/",
    response_model=BitacoraListResponse,
    summary="Bitácora de eventos de gestión (presentación)",
    dependencies=[Depends(require_role(
        "Jefe de Infraestructura",
        "Auxiliar de Infraestructura",
    ))],
)
def listar_bitacora_gestion(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    actor_nombre: Optional[str] = Query(None, description="Filtrar por nombre del operario"),
    tipo_evento: Optional[str] = Query(None, description="Filtrar por categoría de evento"),
    fecha_desde: Optional[date] = Query(None, description="Fecha inicial del rango"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha final del rango"),
    bloque_id: Optional[int] = Query(None, gt=0, description="Filtrar por bloque"),
    piso: Optional[int] = Query(None, ge=0, description="Filtrar por piso"),
    espacio_id: Optional[int] = Query(None, gt=0, description="Filtrar por espacio/aula"),
):
    """Devuelve eventos listos para renderizar en la UI con filtros combinables."""
    query = db.query(Auditoria).options(joinedload(Auditoria.encargado))

    if actor_nombre:
        termino = actor_nombre.strip()
        query = query.filter(Auditoria.actor_nombre.ilike(f"%{termino}%"))
    if tipo_evento:
        query = query.filter(Auditoria.tipo_evento == tipo_evento.strip())
    if fecha_desde:
        inicio = datetime.combine(fecha_desde, time.min)
        query = query.filter(Auditoria.fecha_cambio >= inicio)
    if fecha_hasta:
        fin = datetime.combine(fecha_hasta, time.max)
        query = query.filter(Auditoria.fecha_cambio <= fin)

    query = _aplicar_filtro_ubicacion(query, db, bloque_id, piso, espacio_id)

    total = query.count()
    registros = (
        query.order_by(Auditoria.fecha_cambio.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return BitacoraListResponse(
        total=total,
        items=[a_evento_presentacion(r) for r in registros],
    )
