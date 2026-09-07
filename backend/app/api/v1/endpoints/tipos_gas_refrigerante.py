"""
Endpoints para la entidad TipoGasRefrigerante.
Gestión del catálogo de gases refrigerantes (solo superusuario).
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.models.tipo_gas_refrigerante import TipoGasRefrigerante
from app.models.equipo import Equipo
from app.models.usuario import Usuario
from app.schemas.tipo_gas_refrigerante import (
    TipoGasRefrigeranteCreate,
    TipoGasRefrigeranteUpdate,
    TipoGasRefrigeranteResponse,
)
from app.core.security import require_role, get_current_user

router = APIRouter(prefix="/tipos-gas-refrigerante", tags=["tipos-gas-refrigerante"])

ROLES_SUPERUSUARIO = ("Jefe de Infraestructura",)


@router.get("/", response_model=List[TipoGasRefrigeranteResponse])
def listar_tipos_gas_refrigerante(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Lista todos los tipos de gas refrigerante registrados."""
    return db.query(TipoGasRefrigerante).offset(skip).limit(limit).all()


@router.get("/{tipo_id}", response_model=TipoGasRefrigeranteResponse)
def obtener_tipo_gas_refrigerante(tipo_id: int, db: Session = Depends(get_db)):
    tipo = db.query(TipoGasRefrigerante).filter(TipoGasRefrigerante.id == tipo_id).first()
    if not tipo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El tipo de gas refrigerante con ID {tipo_id} no existe",
        )
    return tipo


@router.post(
    "/",
    response_model=TipoGasRefrigeranteResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(*ROLES_SUPERUSUARIO))],
)
def crear_tipo_gas_refrigerante(
    tipo_in: TipoGasRefrigeranteCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    del current_user
    existente = db.query(TipoGasRefrigerante).filter(
        func.lower(TipoGasRefrigerante.nombre) == func.lower(tipo_in.nombre)
    ).first()
    if existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El refrigerante '{tipo_in.nombre}' ya existe en el catálogo.",
        )

    nuevo = TipoGasRefrigerante(**tipo_in.model_dump())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


@router.put(
    "/{tipo_id}",
    response_model=TipoGasRefrigeranteResponse,
    dependencies=[Depends(require_role(*ROLES_SUPERUSUARIO))],
)
def actualizar_tipo_gas_refrigerante(
    tipo_id: int,
    tipo_in: TipoGasRefrigeranteUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    del current_user
    tipo = db.query(TipoGasRefrigerante).filter(TipoGasRefrigerante.id == tipo_id).first()
    if not tipo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El tipo de gas refrigerante con ID {tipo_id} no existe",
        )

    nombre_anterior = tipo.nombre
    if tipo_in.nombre and tipo_in.nombre != tipo.nombre:
        duplicado = db.query(TipoGasRefrigerante).filter(
            func.lower(TipoGasRefrigerante.nombre) == func.lower(tipo_in.nombre),
            TipoGasRefrigerante.id != tipo_id,
        ).first()
        if duplicado:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El refrigerante '{tipo_in.nombre}' ya existe.",
            )
        tipo.nombre = tipo_in.nombre

        db.query(Equipo).filter(
            func.lower(Equipo.refrigerante) == func.lower(nombre_anterior)
        ).update({Equipo.refrigerante: tipo.nombre}, synchronize_session=False)

    db.commit()
    db.refresh(tipo)
    return tipo


@router.delete(
    "/{tipo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role(*ROLES_SUPERUSUARIO))],
)
def eliminar_tipo_gas_refrigerante(
    tipo_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    del current_user
    tipo = db.query(TipoGasRefrigerante).filter(TipoGasRefrigerante.id == tipo_id).first()
    if not tipo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El tipo de gas refrigerante con ID {tipo_id} no existe",
        )

    equipos_asociados = (
        db.query(func.count(Equipo.id))
        .filter(func.lower(Equipo.refrigerante) == func.lower(tipo.nombre))
        .scalar()
        or 0
    )
    if equipos_asociados > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"No se puede eliminar el refrigerante '{tipo.nombre}' porque está "
                f"asignado a {equipos_asociados} equipo(s) registrado(s) en el sistema."
            ),
        )

    db.delete(tipo)
    db.commit()
