"""
Endpoints para la entidad TipoComponente.
Gestión del catálogo de repuestos e insumos: lectura autenticada y escrituras
restringidas a Jefe y Auxiliar de Infraestructura.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.security import get_current_user, require_role, ROLES_GESTION
from app.db.session import get_db
from app.models.componente_usado import ComponenteUsado
from app.models.tipo_componente import TipoComponente
from app.models.usuario import Usuario
from app.schemas.mantenimiento import INSUMOS_FIJOS_TALLER
from app.schemas.tipo_componente import (
    TipoComponenteCreate,
    TipoComponenteResponse,
    TipoComponenteUpdate,
)

router = APIRouter(prefix="/tipo_componentes", tags=["tipo_componentes"])

@router.get(
    "/",
    response_model=List[TipoComponenteResponse],
    dependencies=[Depends(get_current_user)],
)
def listar_tipo_componentes(
    fijos: bool = Query(False, description="Si es true, devuelve solo los 3 insumos fijos del taller"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
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
        componentes = query.order_by(TipoComponente.id).offset(skip).limit(limit).all()
        return componentes
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al consultar el catálogo de componentes: {str(e)}",
        )


@router.get(
    "/{tipo_id}",
    response_model=TipoComponenteResponse,
    dependencies=[Depends(get_current_user)],
)
def obtener_tipo_componente(tipo_id: int, db: Session = Depends(get_db)):
    """Obtiene un tipo de componente por ID."""
    tipo = db.query(TipoComponente).filter(TipoComponente.id == tipo_id).first()
    if not tipo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El tipo de componente con ID {tipo_id} no existe",
        )
    return tipo


@router.post(
    "/",
    response_model=TipoComponenteResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(*ROLES_GESTION))],
)
def crear_tipo_componente(
    tipo_in: TipoComponenteCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Crea un nuevo tipo de componente o insumo (Jefe/Auxiliar de Infraestructura)."""
    del current_user
    try:
        tipo_existente = (
            db.query(TipoComponente)
            .filter(func.lower(TipoComponente.nombre) == func.lower(tipo_in.nombre))
            .first()
        )
        if tipo_existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El tipo de componente '{tipo_in.nombre}' ya existe en el catálogo.",
            )

        nuevo_tipo = TipoComponente(**tipo_in.model_dump())
        db.add(nuevo_tipo)
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
            detail=f"Error al crear tipo de componente: {str(e)}",
        )


@router.put(
    "/{tipo_id}",
    response_model=TipoComponenteResponse,
    dependencies=[Depends(require_role(*ROLES_GESTION))],
)
def actualizar_tipo_componente(
    tipo_id: int,
    tipo_in: TipoComponenteUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Actualiza el nombre de un tipo de componente (Jefe/Auxiliar de Infraestructura)."""
    del current_user
    tipo = db.query(TipoComponente).filter(TipoComponente.id == tipo_id).first()
    if not tipo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El tipo de componente con ID {tipo_id} no existe",
        )

    try:
        if tipo_in.nombre and tipo_in.nombre != tipo.nombre:
            tipo_nombre_existe = (
                db.query(TipoComponente)
                .filter(
                    func.lower(TipoComponente.nombre) == func.lower(tipo_in.nombre),
                    TipoComponente.id != tipo_id,
                )
                .first()
            )
            if tipo_nombre_existe:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El tipo de componente '{tipo_in.nombre}' ya existe.",
                )

        datos_update = tipo_in.model_dump(exclude_unset=True)
        for campo, valor in datos_update.items():
            if valor is not None:
                setattr(tipo, campo, valor)

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
            detail=f"Error al actualizar tipo de componente: {str(e)}",
        )


@router.delete(
    "/{tipo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role(*ROLES_GESTION))],
)
def eliminar_tipo_componente(
    tipo_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Elimina un tipo de componente si no está en uso (Jefe/Auxiliar de Infraestructura)."""
    del current_user
    tipo = db.query(TipoComponente).filter(TipoComponente.id == tipo_id).first()
    if not tipo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El tipo de componente con ID {tipo_id} no existe",
        )

    usos_asociados = (
        db.query(func.count(ComponenteUsado.id))
        .filter(ComponenteUsado.repuesto_utilizado_id == tipo_id)
        .scalar()
        or 0
    )
    if usos_asociados > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"No se puede eliminar el tipo de componente '{tipo.nombre}' porque está "
                f"asociado a {usos_asociados} registro(s) en mantenimientos realizados."
            ),
        )

    try:
        db.delete(tipo)
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al eliminar tipo de componente: {str(e)}",
        )
