"""
Endpoints para la entidad TipoEquipo.
Gestión de tipos de equipos de climatización (solo superusuario).
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.models.tipo_equipo import TipoEquipo
from app.models.equipo import Equipo
from app.models.usuario import Usuario
from app.schemas.tipo_equipo import (
    TipoEquipoCreate,
    TipoEquipoUpdate,
    TipoEquipoResponse,
)
from app.schemas.auditoria import EventoAuditoriaCreate, TipoEventoEnum
from app.core.security import require_role, get_current_user
from app.services.audit_event_processor import procesar_evento_auditoria
from app.services.audit_classifier import inferir_campo_crud

router = APIRouter(prefix="/tipos-equipo", tags=["tipos-equipo"])

ROLES_SUPERUSUARIO = ("Jefe de Infraestructura",)


@router.get("/", response_model=List[TipoEquipoResponse])
def listar_tipos_equipo(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Lista todos los tipos de equipos registrados."""
    tipos = db.query(TipoEquipo).offset(skip).limit(limit).all()
    return tipos


@router.get("/{tipo_id}", response_model=TipoEquipoResponse)
def obtener_tipo_equipo(tipo_id: int, db: Session = Depends(get_db)):
    """Obtiene un tipo de equipo por ID."""
    tipo = db.query(TipoEquipo).filter(TipoEquipo.id == tipo_id).first()
    if not tipo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El tipo de equipo con ID {tipo_id} no existe",
        )
    return tipo


@router.post(
    "/",
    response_model=TipoEquipoResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(*ROLES_SUPERUSUARIO))],
)
def crear_tipo_equipo(
    tipo_in: TipoEquipoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Crea un nuevo tipo de equipo (solo superusuario)."""
    try:
        tipo_existente = db.query(TipoEquipo).filter(
            func.lower(TipoEquipo.nombre) == func.lower(tipo_in.nombre)
        ).first()
        if tipo_existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El tipo de equipo '{tipo_in.nombre}' ya existe en el catálogo.",
            )

        nuevo_tipo = TipoEquipo(**tipo_in.model_dump())
        db.add(nuevo_tipo)
        db.flush()

        procesar_evento_auditoria(
            db,
            EventoAuditoriaCreate(
                tipo_evento=TipoEventoEnum.CRUD_TIPOS_EQUIPO,
                encargado_id=current_user.id,
                registro_id=nuevo_tipo.id,
                tabla_afectada="tipos_equipos",
                campo=inferir_campo_crud("create"),
                estado_nuevo=tipo_in.nombre,
                recurso_descripcion=tipo_in.nombre,
            ),
            flush=True,
        )

        db.commit()
        db.refresh(nuevo_tipo)
        return nuevo_tipo

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al crear tipo de equipo: {str(e)}",
        )


@router.put(
    "/{tipo_id}",
    response_model=TipoEquipoResponse,
    dependencies=[Depends(require_role(*ROLES_SUPERUSUARIO))],
)
def actualizar_tipo_equipo(
    tipo_id: int,
    tipo_in: TipoEquipoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Actualiza el nombre de un tipo de equipo (solo superusuario)."""
    tipo = db.query(TipoEquipo).filter(TipoEquipo.id == tipo_id).first()
    if not tipo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El tipo de equipo con ID {tipo_id} no existe",
        )

    try:
        nombre_anterior = tipo.nombre
        if tipo_in.nombre and tipo_in.nombre != tipo.nombre:
            tipo_nombre_existe = db.query(TipoEquipo).filter(
                func.lower(TipoEquipo.nombre) == func.lower(tipo_in.nombre),
                TipoEquipo.id != tipo_id,
            ).first()
            if tipo_nombre_existe:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El tipo de equipo '{tipo_in.nombre}' ya existe.",
                )

        datos_update = tipo_in.model_dump(exclude_unset=True)
        for campo, valor in datos_update.items():
            if valor is not None:
                setattr(tipo, campo, valor)

        procesar_evento_auditoria(
            db,
            EventoAuditoriaCreate(
                tipo_evento=TipoEventoEnum.CRUD_TIPOS_EQUIPO,
                encargado_id=current_user.id,
                registro_id=tipo_id,
                tabla_afectada="tipos_equipos",
                campo=inferir_campo_crud("update"),
                estado_anterior=nombre_anterior,
                estado_nuevo=tipo.nombre,
                recurso_descripcion=tipo.nombre,
            ),
            flush=True,
        )

        db.commit()
        db.refresh(tipo)
        return tipo

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al actualizar tipo de equipo: {str(e)}",
        )


@router.delete(
    "/{tipo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role(*ROLES_SUPERUSUARIO))],
)
def eliminar_tipo_equipo(
    tipo_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Elimina un tipo de equipo si no está en uso (solo superusuario)."""
    tipo = db.query(TipoEquipo).filter(TipoEquipo.id == tipo_id).first()
    if not tipo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El tipo de equipo con ID {tipo_id} no existe",
        )

    equipos_asociados = (
        db.query(func.count(Equipo.id))
        .filter(Equipo.tipo_equipo_id == tipo_id)
        .scalar()
        or 0
    )
    if equipos_asociados > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"No se puede eliminar el tipo de equipo '{tipo.nombre}' porque está "
                f"asignado a {equipos_asociados} equipo(s) registrado(s) en el sistema."
            ),
        )

    nombre_tipo = tipo.nombre
    try:
        db.delete(tipo)
        db.flush()

        procesar_evento_auditoria(
            db,
            EventoAuditoriaCreate(
                tipo_evento=TipoEventoEnum.CRUD_TIPOS_EQUIPO,
                encargado_id=current_user.id,
                registro_id=tipo_id,
                tabla_afectada="tipos_equipos",
                campo=inferir_campo_crud("delete"),
                estado_anterior=nombre_tipo,
                recurso_descripcion=nombre_tipo,
            ),
            flush=True,
        )

        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al eliminar tipo de equipo: {str(e)}",
        )
