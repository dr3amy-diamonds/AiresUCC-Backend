"""
Capa de Servicios para la Entidad Equipo.
Lógica de negocio para equipos de aire acondicionado.
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func

from app.models.equipo import Equipo
from app.schemas.equipo_new import EquipoCreate, EquipoUpdate, EquipoResponse


def obtener_equipo_por_id(db: Session, equipo_id: int) -> Optional[Equipo]:
    """Obtiene un equipo por su ID."""
    return db.query(Equipo).filter(Equipo.id == equipo_id).first()


def obtener_equipo_por_codigo(db: Session, codigo_activo: str) -> Optional[Equipo]:
    """Obtiene un equipo por su código de activo."""
    return db.query(Equipo).filter(Equipo.codigo_activo == codigo_activo).first()


def obtener_equipos(db: Session, skip: int = 0, limit: int = 10) -> tuple[List[Equipo], int]:
    """Obtiene lista paginada de equipos."""
    total = db.query(func.count(Equipo.id)).scalar() or 0
    equipos = db.query(Equipo).offset(skip).limit(limit).all()
    return equipos, total


def obtener_equipos_por_espacio(db: Session, espacio_id: int) -> List[Equipo]:
    """Obtiene todos los equipos de un espacio específico."""
    return db.query(Equipo).filter(Equipo.espacio_id == espacio_id).all()


def obtener_equipos_por_estado(db: Session, estado: str, skip: int = 0, limit: int = 10) -> tuple[List[Equipo], int]:
    """Obtiene equipos filtrados por estado."""
    total = db.query(func.count(Equipo.id)).filter(Equipo.estado == estado).scalar() or 0
    equipos = db.query(Equipo).filter(Equipo.estado == estado).offset(skip).limit(limit).all()
    return equipos, total


def crear_equipo(db: Session, equipo_in: EquipoCreate) -> Equipo:
    """Crea un nuevo equipo."""
    try:
        db_equipo = Equipo(**equipo_in.model_dump())
        db.add(db_equipo)
        db.commit()
        db.refresh(db_equipo)
        return db_equipo
    except IntegrityError as e:
        db.rollback()
        raise IntegrityError(
            statement="Fallo al crear equipo",
            params={"codigo_activo": equipo_in.codigo_activo},
            orig=e.orig
        ) from e


def actualizar_equipo(db: Session, db_obj: Equipo, obj_in: EquipoUpdate) -> Equipo:
    """Actualiza un equipo existente."""
    try:
        datos = obj_in.model_dump(exclude_unset=True)
        for campo, valor in datos.items():
            setattr(db_obj, campo, valor)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    except IntegrityError as e:
        db.rollback()
        raise IntegrityError(
            statement="Fallo al actualizar equipo",
            params={"equipo_id": db_obj.id},
            orig=e.orig
        ) from e


def eliminar_equipo(db: Session, equipo_id: int) -> bool:
    """Elimina (marca como baja) un equipo."""
    equipo = obtener_equipo_por_id(db, equipo_id)
    if equipo:
        equipo.estado = "Dado de baja"
        db.commit()
        return True
    return False


def cambiar_estado_equipo(db: Session, equipo_id: int, nuevo_estado: str) -> Optional[Equipo]:
    """Cambia el estado de un equipo."""
    estados_validos = ["Operativo", "En reparacion", "Inactivo", "Dado de baja"]
    if nuevo_estado not in estados_validos:
        raise ValueError(f"Estado inválido. Debe ser uno de: {', '.join(estados_validos)}")

    equipo = obtener_equipo_por_id(db, equipo_id)
    if equipo:
        equipo.estado = nuevo_estado
        db.commit()
        db.refresh(equipo)
        return equipo
    return None

