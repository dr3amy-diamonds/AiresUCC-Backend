"""
Endpoints para la entidad Equipo.
API REST para la gestión integral de equipos de aire acondicionado.
Actualizado para el MVP: Soporte completo para tonelaje, serial y fechas.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc

from app.db.session import get_db
from app.models.equipo import Equipo
from app.models.mantenimiento import Mantenimiento

from app.schemas.equipo import EquipoCreate, EquipoUpdate, EquipoResponse, EquipoListResponse, ActivarEquipoRequest
from app.schemas.mantenimiento import MantenimientoHistorialEquipoResponse
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
        "items": equipos
    }

@router.get("/{equipo_id}/mantenimientos", response_model=List[MantenimientoHistorialEquipoResponse])
def listar_mantenimientos_equipo(
    equipo_id: int,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Historial de intervenciones técnicas de un equipo."""
    equipo = obtener_equipo_por_id(db, equipo_id)
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")

    mantenimientos = (
        db.query(Mantenimiento)
        .options(
            joinedload(Mantenimiento.encargado),
            joinedload(Mantenimiento.tipo),
        )
        .filter(Mantenimiento.equipo_id == equipo_id)
        .order_by(desc(Mantenimiento.fecha_mantenimiento))
        .limit(limit)
        .all()
    )

    return [
        MantenimientoHistorialEquipoResponse(
            id=m.id,
            fecha_mantenimiento=m.fecha_mantenimiento,
            detalle_mantenimiento=m.detalle_mantenimiento,
            tipo_nombre=m.tipo.nombre if m.tipo else None,
            tecnico_nombre=m.encargado.nombre if m.encargado else None,
        )
        for m in mantenimientos
    ]


@router.get("/{equipo_id}", response_model=EquipoResponse)
def leer_equipo(equipo_id: int, db: Session = Depends(get_db)):
    """Busca un equipo específico por su ID único."""
    equipo = obtener_equipo_por_id(db, equipo_id)
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    return EquipoResponse.model_validate(equipo)

@router.get("/codigo/{codigo}", response_model=EquipoResponse)
def leer_equipo_por_codigo(codigo: str, db: Session = Depends(get_db)):
    """Busca un equipo usando la placa de inventario oficial."""
    equipo = obtener_equipo_por_codigo(db, codigo)
    if not equipo:
        raise HTTPException(status_code=404, detail="Código de activo no registrado")
    return EquipoResponse.model_validate(equipo)

@router.get("/espacio/{espacio_id}", response_model=List[EquipoResponse])
def listar_equipos_por_espacio(espacio_id: int, db: Session = Depends(get_db)):
    """Lista todos los equipos instalados en un espacio físico específico."""
    equipos = obtener_equipos_por_espacio(db, espacio_id)
    return [EquipoResponse.model_validate(e) for e in equipos]

@router.get("/estado/{estado}", response_model=List[EquipoResponse])
def listar_equipos_por_estado(estado: str, db: Session = Depends(get_db)):
    """Filtra los equipos según su estado operativo (Operativo, En reparación, etc.)."""
    equipos = obtener_equipos_por_estado(db, estado)
    return [EquipoResponse.model_validate(e) for e in equipos]

@router.post("/", response_model=EquipoResponse, status_code=status.HTTP_201_CREATED)
def crear_equipo_endpoint(
    equipo_in: EquipoCreate,
    db: Session = Depends(get_db)
):
    """Registra un nuevo aire acondicionado en el sistema."""
    try:
        equipo = crear_equipo(db, equipo_in)
        return EquipoResponse.model_validate(equipo)
    except ValueError as ve:
        # Capturar errores de validación (duplicados, etc)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{equipo_id}", response_model=EquipoResponse)
def actualizar_equipo_endpoint(
    equipo_id: int,
    equipo_in: EquipoUpdate,
    db: Session = Depends(get_db)
):
    """Actualiza los datos de un equipo existente."""
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
    """Cambia el estado de un equipo de forma rápida."""
    try:
        equipo = cambiar_estado_equipo(db, equipo_id, nuevo_estado)
        if not equipo:
            raise HTTPException(status_code=404, detail="Equipo no encontrado")
        return EquipoResponse.model_validate(equipo)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{equipo_id}", status_code=status.HTTP_204_NO_CONTENT)
@router.delete("/{equipo_id}", status_code=status.HTTP_200_OK)
def eliminar_equipo_endpoint(equipo_id: int, db: Session = Depends(get_db)):
    """Elimina un equipo del sistema (Baja de activo)."""
    # 1. Verificar si el aire existe en la base de datos
    equipo = obtener_equipo_por_id(db, equipo_id)
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")

    try:
        # 2. Intentar ejecutar la eliminación lógica/física en el servicio
        eliminar_equipo(db, equipo_id)

        # Forzamos un flush/commit si el servicio no lo hace,
        # para obligar a PostgreSQL a validar las llaves foráneas de inmediato
        db.flush()

        return {"detail": "El equipo fue eliminado correctamente del inventario."}

    except Exception as e:
        # 3. Si PostgreSQL frena el borrado porque el aire tiene mantenimientos registrados
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede eliminar este equipo porque tiene un historial de mantenimientos asociado en AuraData."
        )

@router.post("/activar", response_model=EquipoResponse, status_code=status.HTTP_200_OK)
def activar_equipo_endpoint(request: ActivarEquipoRequest, db: Session = Depends(get_db)):
    """Activa un equipo cambiando su estado a 'Operativo' usando su código de activo."""
    try:
        # Convertir el código a string para buscar en la BD (ya que el modelo lo define como String)
        codigo_str = str(request.codigo_activo)
        equipo = obtener_equipo_por_codigo(db, codigo_str)
        
        if not equipo:
            raise HTTPException(status_code=404, detail="Equipo no encontrado con ese código de activo")
        
        # Actualizar el estado
        equipo.estado = "Operativo"
        db.commit()
        db.refresh(equipo)
        
        return EquipoResponse.model_validate(equipo)
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al activar el equipo: {str(e)}")
