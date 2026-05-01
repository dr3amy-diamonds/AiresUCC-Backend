"""
Endpoints para la entidad Equipo.
API REST para gestión de equipos de aire acondicionado.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.equipo import Equipo
from app.schemas.equipo_new import EquipoCreate, EquipoUpdate, EquipoResponse, EquipoListResponse
from app.services.equipo import (
    obtener_equipo_por_id,
    obtener_equipo_por_codigo,
    obtener_equipos,
    obtener_equipos_por_espacio,
    obtener_equipos_por_estado,
    crear_equipo,
    actualizar_equipo,
    eliminar_equipo,
    cambiar_estado_equipo
)

router = APIRouter(prefix="/equipos", tags=["equipos"])


@router.get("/", response_model=EquipoListResponse)
def listar_equipos(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Lista todos los equipos con paginación."""
    equipos, total = obtener_equipos(db, skip=skip, limit=limit)
    return {
        "total": total,
        "page": skip // limit + 1,
        "size": limit,
        "items": [EquipoResponse.model_validate(e) for e in equipos]
    }


@router.get("/{equipo_id}", response_model=EquipoResponse)
def obtener_equipo(equipo_id: int, db: Session = Depends(get_db)):
    """Obtiene un equipo específico por ID."""
    equipo = obtener_equipo_por_id(db, equipo_id)
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    return EquipoResponse.model_validate(equipo)


@router.get("/codigo/{codigo_activo}", response_model=EquipoResponse)
def obtener_equipo_por_codigo_endpoint(codigo_activo: str, db: Session = Depends(get_db)):
    """Obtiene un equipo por su código de activo."""
    equipo = obtener_equipo_por_codigo(db, codigo_activo)
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    return EquipoResponse.model_validate(equipo)


@router.get("/espacio/{espacio_id}", response_model=List[EquipoResponse])
def obtener_equipos_espacio(espacio_id: int, db: Session = Depends(get_db)):
    """Obtiene todos los equipos de un espacio."""
    equipos = obtener_equipos_por_espacio(db, espacio_id)
    return [EquipoResponse.model_validate(e) for e in equipos]


@router.get("/estado/{estado}", response_model=EquipoListResponse)
def obtener_equipos_estado(
    estado: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Obtiene equipos filtrados por estado."""
    equipos, total = obtener_equipos_por_estado(db, estado, skip=skip, limit=limit)
    return {
        "total": total,
        "page": skip // limit + 1,
        "size": limit,
        "items": [EquipoResponse.model_validate(e) for e in equipos]
    }


@router.post("/", response_model=EquipoResponse, status_code=201)
def crear_equipo_endpoint(equipo_in: EquipoCreate, db: Session = Depends(get_db)):
    """Crea un nuevo equipo."""
    try:
        equipo = crear_equipo(db, equipo_in)
        return EquipoResponse.model_validate(equipo)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{equipo_id}", response_model=EquipoResponse)
def actualizar_equipo_endpoint(
    equipo_id: int,
    equipo_in: EquipoUpdate,
    db: Session = Depends(get_db)
):
    """Actualiza un equipo existente."""
    equipo = obtener_equipo_por_id(db, equipo_id)
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")

    try:
        equipo_actualizado = actualizar_equipo(db, equipo, equipo_in)
        return EquipoResponse.model_validate(equipo_actualizado)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{equipo_id}/estado/{nuevo_estado}", response_model=EquipoResponse)
def cambiar_estado_endpoint(
    equipo_id: int,
    nuevo_estado: str,
    db: Session = Depends(get_db)
):
    """Cambia el estado de un equipo."""
    equipo = cambiar_estado_equipo(db, equipo_id, nuevo_estado)
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    return EquipoResponse.model_validate(equipo)


@router.delete("/{equipo_id}", status_code=204)
def eliminar_equipo_endpoint(equipo_id: int, db: Session = Depends(get_db)):
    """Elimina (marca como baja) un equipo."""
    if not eliminar_equipo(db, equipo_id):
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    return None

