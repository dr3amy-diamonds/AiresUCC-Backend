"""
Capa de Servicios para la Entidad Equipo.
Lógica de negocio para equipos de aire acondicionado en AuraData Analytics.
"""

from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func

from app.models.equipo import Equipo
# IMPORTANTE: Corregido para que apunte al schema actualizado
from app.schemas.equipo import EquipoCreate, EquipoUpdate, EquipoResponse

def obtener_equipo_por_id(db: Session, equipo_id: int) -> Optional[Equipo]:
    return db.query(Equipo).options(
        joinedload(Equipo.marca),
        joinedload(Equipo.espacio),
        joinedload(Equipo.tipo)
    ).filter(Equipo.id == equipo_id).first()

def obtener_equipo_por_codigo(db: Session, codigo_activo: str) -> Optional[Equipo]:
    return db.query(Equipo).options(
        joinedload(Equipo.marca),
        joinedload(Equipo.espacio),
        joinedload(Equipo.tipo)
    ).filter(Equipo.codigo_activo == codigo_activo).first()

def obtener_equipos(db: Session, skip: int = 0, limit: int = 10) -> tuple[List[Equipo], int]:
    total = db.query(func.count(Equipo.id)).scalar() or 0
    equipos = db.query(Equipo).options(
        joinedload(Equipo.marca),
        joinedload(Equipo.espacio),
        joinedload(Equipo.tipo)
    ).offset(skip).limit(limit).all()
    return equipos, total

def obtener_equipos_por_espacio(db: Session, espacio_id: int) -> List[Equipo]:
    return db.query(Equipo).options(
        joinedload(Equipo.marca),
        joinedload(Equipo.espacio),
        joinedload(Equipo.tipo)
    ).filter(Equipo.espacio_id == espacio_id).all()

def obtener_equipos_por_estado(db: Session, estado: str) -> List[Equipo]:
    return db.query(Equipo).options(
        joinedload(Equipo.marca),
        joinedload(Equipo.espacio),
        joinedload(Equipo.tipo)
    ).filter(Equipo.estado == estado).all()

def crear_equipo(db: Session, equipo_in: EquipoCreate) -> Equipo:
    """
    Crea un nuevo equipo con validaciones de unicidad para codigo_activo y numero_serie.

    Validaciones:
    - codigo_activo debe ser único
    - numero_serie debe ser único (si se proporciona)
    """
    try:
        # 1. VALIDACIÓN: Verificar que codigo_activo no existe
        equipo_codigo_existe = db.query(Equipo).filter(
            Equipo.codigo_activo == equipo_in.codigo_activo
        ).first()

        if equipo_codigo_existe:
            raise ValueError(f"El codigo_activo '{equipo_in.codigo_activo}' ya existe. Use un código de inventario único.")

        # 2. VALIDACIÓN: Verificar que numero_serie no existe (si se proporciona)
        if equipo_in.numero_serie:
            equipo_serie_existe = db.query(Equipo).filter(
                Equipo.numero_serie == equipo_in.numero_serie
            ).first()

            if equipo_serie_existe:
                raise ValueError(f"El numero_serie '{equipo_in.numero_serie}' ya existe. El número de serie debe ser único.")

        # 3. Crear el equipo
        datos_equipo = equipo_in.model_dump()
        db_obj = Equipo(**datos_equipo)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    except ValueError as ve:
        db.rollback()
        raise ve
    except IntegrityError as e:
        db.rollback()
        raise IntegrityError(
            statement="Fallo al crear equipo",
            params={"codigo_activo": equipo_in.codigo_activo},
            orig=e.orig
        ) from e

def actualizar_equipo(db: Session, db_obj: Equipo, obj_in: EquipoUpdate) -> Equipo:
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
    equipo = obtener_equipo_por_id(db, equipo_id)
    if equipo:
        equipo.estado = "Dado de baja"
        db.commit()
        return True
    return False

def cambiar_estado_equipo(db: Session, equipo_id: int, nuevo_estado: str) -> Optional[Equipo]:
    estados_validos = ["Operativo", "En reparacion", "Inactivo", "Dado de baja"]
    if nuevo_estado in estados_validos:
        equipo = obtener_equipo_por_id(db, equipo_id)
        if equipo:
            equipo.estado = nuevo_estado
            db.commit()
            db.refresh(equipo)
        return equipo
    return None