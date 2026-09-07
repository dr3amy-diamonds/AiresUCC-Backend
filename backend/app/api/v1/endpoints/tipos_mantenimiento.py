"""Endpoints para la entidad TipoMantenimiento (solo superusuario en escrituras)."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.security import get_current_user, require_role
from app.db.session import get_db
from app.models.mantenimiento import Mantenimiento
from app.models.programacion import Programacion
from app.models.tipo_mantenimiento import TipoMantenimiento
from app.models.usuario import Usuario
from app.schemas.auditoria import EventoAuditoriaCreate, TipoEventoEnum
from app.schemas.tipo_mantenimiento import (
    TipoMantenimientoCreate,
    TipoMantenimientoResponse,
    TipoMantenimientoUpdate,
)
from app.services.audit_classifier import inferir_campo_crud
from app.services.audit_event_processor import procesar_evento_auditoria

router = APIRouter(prefix="/tipos-mantenimiento", tags=["tipos-mantenimiento"])

ROLES_SUPERUSUARIO = ("Jefe de Infraestructura",)


@router.get("/", response_model=List[TipoMantenimientoResponse])
def listar_tipos_mantenimiento(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Lista los tipos de mantenimiento disponibles para formularios."""
    return (
        db.query(TipoMantenimiento)
        .order_by(TipoMantenimiento.id)
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/{tipo_id}", response_model=TipoMantenimientoResponse)
def obtener_tipo_mantenimiento(tipo_id: int, db: Session = Depends(get_db)):
    """Obtiene un tipo de mantenimiento por ID."""
    tipo = db.query(TipoMantenimiento).filter(TipoMantenimiento.id == tipo_id).first()
    if not tipo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El tipo de mantenimiento con ID {tipo_id} no existe",
        )
    return tipo


@router.post(
    "/",
    response_model=TipoMantenimientoResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(*ROLES_SUPERUSUARIO))],
)
def crear_tipo_mantenimiento(
    tipo_in: TipoMantenimientoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Crea un nuevo tipo de mantenimiento (solo superusuario)."""
    try:
        tipo_existente = (
            db.query(TipoMantenimiento)
            .filter(func.lower(TipoMantenimiento.nombre) == func.lower(tipo_in.nombre))
            .first()
        )
        if tipo_existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El tipo de mantenimiento '{tipo_in.nombre}' ya existe en el catálogo.",
            )

        nuevo_tipo = TipoMantenimiento(**tipo_in.model_dump())
        db.add(nuevo_tipo)
        db.flush()

        procesar_evento_auditoria(
            db,
            EventoAuditoriaCreate(
                tipo_evento=TipoEventoEnum.CRUD_TIPOS_MANTENIMIENTO,
                encargado_id=current_user.id,
                registro_id=nuevo_tipo.id,
                tabla_afectada="tipos_mantenimiento",
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
            detail=f"Error al crear tipo de mantenimiento: {str(e)}",
        )


@router.put(
    "/{tipo_id}",
    response_model=TipoMantenimientoResponse,
    dependencies=[Depends(require_role(*ROLES_SUPERUSUARIO))],
)
def actualizar_tipo_mantenimiento(
    tipo_id: int,
    tipo_in: TipoMantenimientoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Actualiza un tipo de mantenimiento (solo superusuario)."""
    tipo = db.query(TipoMantenimiento).filter(TipoMantenimiento.id == tipo_id).first()
    if not tipo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El tipo de mantenimiento con ID {tipo_id} no existe",
        )

    try:
        nombre_anterior = tipo.nombre
        if tipo_in.nombre and tipo_in.nombre != tipo.nombre:
            tipo_nombre_existe = (
                db.query(TipoMantenimiento)
                .filter(
                    func.lower(TipoMantenimiento.nombre) == func.lower(tipo_in.nombre),
                    TipoMantenimiento.id != tipo_id,
                )
                .first()
            )
            if tipo_nombre_existe:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El tipo de mantenimiento '{tipo_in.nombre}' ya existe.",
                )

        datos_update = tipo_in.model_dump(exclude_unset=True)
        for campo, valor in datos_update.items():
            setattr(tipo, campo, valor)

        procesar_evento_auditoria(
            db,
            EventoAuditoriaCreate(
                tipo_evento=TipoEventoEnum.CRUD_TIPOS_MANTENIMIENTO,
                encargado_id=current_user.id,
                registro_id=tipo_id,
                tabla_afectada="tipos_mantenimiento",
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
            detail=f"Error al actualizar tipo de mantenimiento: {str(e)}",
        )


@router.delete(
    "/{tipo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role(*ROLES_SUPERUSUARIO))],
)
def eliminar_tipo_mantenimiento(
    tipo_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Elimina un tipo de mantenimiento si no está en uso (solo superusuario)."""
    tipo = db.query(TipoMantenimiento).filter(TipoMantenimiento.id == tipo_id).first()
    if not tipo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El tipo de mantenimiento con ID {tipo_id} no existe",
        )

    mantenimientos_asociados = (
        db.query(func.count(Mantenimiento.id))
        .filter(Mantenimiento.tipo_mantenimiento_id == tipo_id)
        .scalar()
        or 0
    )
    programaciones_asociadas = (
        db.query(func.count(Programacion.id))
        .filter(Programacion.tipo_mantenimiento_id == tipo_id)
        .scalar()
        or 0
    )

    if mantenimientos_asociados > 0 or programaciones_asociadas > 0:
        partes = []
        if mantenimientos_asociados > 0:
            partes.append(
                f"{mantenimientos_asociados} mantenimiento(s) registrado(s)"
            )
        if programaciones_asociadas > 0:
            partes.append(
                f"{programaciones_asociadas} programación(es) activa(s) o histórica(s)"
            )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"No se puede eliminar el tipo de mantenimiento '{tipo.nombre}' porque "
                f"tiene registros asociados: {', '.join(partes)}."
            ),
        )

    nombre_tipo = tipo.nombre
    try:
        db.delete(tipo)
        db.flush()

        procesar_evento_auditoria(
            db,
            EventoAuditoriaCreate(
                tipo_evento=TipoEventoEnum.CRUD_TIPOS_MANTENIMIENTO,
                encargado_id=current_user.id,
                registro_id=tipo_id,
                tabla_afectada="tipos_mantenimiento",
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
            detail=f"Error al eliminar tipo de mantenimiento: {str(e)}",
        )
