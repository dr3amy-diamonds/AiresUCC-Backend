"""
Capa de Servicios para la Entidad Programación de Mantenimiento.

Este módulo encapsula lógica de negocio para programaciones:
- Creación de cronogramas futuros
- ** CRÍTICO: Generación automática basada en frecuencia_dias **
- Cambio de estado (Pendiente → Completado → Vencido)
- Listado con filtros por estado
- Vinculación con mantenimientos completados

Arquitectura:
- Lógica de negocio separada de rutas
- Validación de integridad referencial
- Cálculo automático de próxima fecha de mantenimiento
- Estados: Pendiente, Completado, Cancelado, Vencido

ALGORITMO DE GENERACIÓN:
1. Lee frecuencia_dias del tipo_mantenimiento
2. Calcula fecha_programada = hoy + frecuencia_dias
3. Crea nueva programación automáticamente
4. Ambiente: Cronograma nunca se "agota", genera cadena infinita
"""

from typing import Optional, List, Tuple
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, and_, or_

from app.models.programacion import Programacion
from app.models.mantenimiento import Mantenimiento
from app.models.equipo import Equipo
from app.models.tipo_mantenimiento import TipoMantenimiento
from app.schemas.programacion import (
    ProgramacionCreate,
    ProgramacionUpdate,
    EstadoProgramacionEnum
)
from app.schemas.auditoria import EventoAuditoriaCreate, TipoEventoEnum
from app.services.audit_event_processor import procesar_evento_auditoria


# ============================================================================
# FUNCIONES DE LECTURA (READ)
# ============================================================================

def obtener_programacion_por_id(db: Session, programacion_id: int) -> Optional[Programacion]:
    """
    Obtiene una programación por su ID.

    Args:
        db (Session): Sesión de SQLAlchemy
        programacion_id (int): ID de la programación

    Returns:
        Optional[Programacion]: Objeto encontrado o None
    """
    return db.query(Programacion).filter(
        Programacion.id == programacion_id
    ).first()


def listar_programaciones(
    db: Session,
    skip: int = 0,
    limit: int = 10,
    estado: Optional[str] = None,
    equipo_id: Optional[int] = None,
    encargado_id: Optional[int] = None,
    solo_vencidas: bool = False,
    anio: Optional[int] = None,
) -> Tuple[List[Programacion], int, int]:
    """
    Obtiene lista paginada de programaciones con filtros.

    IMPORTANTE: Marca automáticamente como "Vencido" si fecha < hoy

    Args:
        db (Session): Sesión de SQLAlchemy
        skip (int): Offset para paginación
        limit (int): Límite de registros (máximo 100)
        estado (Optional[str]): Filtrar por estado específico
        equipo_id (Optional[int]): Filtrar por equipo
        encargado_id (Optional[int]): Filtrar por técnico asignado
        solo_vencidas (bool): Si True, retorna solo las vencidas

    Returns:
        Tuple: (lista de programaciones, total, pendientes_vencidas)
            - pendientes_vencidas: Cantidad de Pendientes que ya deberían estar hechas
    """
    # Construir query base
    query = db.query(Programacion)

    # Aplicar filtros
    if equipo_id is not None:
        query = query.filter(Programacion.equipo_id == equipo_id)

    if encargado_id is not None:
        query = query.filter(Programacion.encargado_id == encargado_id)

    if anio is not None:
        query = query.filter(func.date_part('year', Programacion.fecha_programada) == anio)

    if solo_vencidas:
        hoy = datetime.now().date()
        query = query.filter(
            and_(
                Programacion.fecha_programada < hoy,
                Programacion.estado == EstadoProgramacionEnum.PENDIENTE.value
            )
        )
    elif estado is not None:
        query = query.filter(Programacion.estado == estado)

    # Contar total
    total = query.count()

    # Contar pendientes vencidas
    hoy = datetime.now().date()
    pendientes_vencidas = (
        db.query(func.count(Programacion.id))
        .filter(
            and_(
                Programacion.fecha_programada < hoy,
                Programacion.estado == EstadoProgramacionEnum.PENDIENTE.value
            )
        )
        .scalar() or 0
    )

    # Paginar ordenadas por fecha (próximas primero si Pendientes)
    programaciones = (
        query
        .order_by(Programacion.fecha_programada)
        .offset(skip)
        .limit(min(limit, 100))
        .all()
    )

    return programaciones, total, pendientes_vencidas


def obtener_programaciones_por_estado(
    db: Session,
    estado: str,
    limit: int = 50
) -> List[Programacion]:
    """
    Obtiene programaciones filtradas por estado específico.

    Útil para dashboards agrupados por estado.

    Args:
        db (Session): Sesión de SQLAlchemy
        estado (str): Estado a filtrar (Pendiente, Completado, etc)
        limit (int): Máximo de registros

    Returns:
        List[Programacion]: Programaciones con ese estado
    """
    return (
        db.query(Programacion)
        .filter(Programacion.estado == estado)
        .order_by(Programacion.fecha_programada)
        .limit(limit)
        .all()
    )


def obtener_programaciones_vencidas(
    db: Session,
    limit: int = 50
) -> List[Programacion]:
    """
    Obtiene programaciones pendientes que ya deberían estar completadas.

    CRÍTICO para alertas: Estas son mantenimientos ATRASADOS.

    Args:
        db (Session): Sesión de SQLAlchemy
        limit (int): Máximo de registros

    Returns:
        List[Programacion]: Programaciones vencidas (Pendiente + fecha < hoy)
    """
    hoy = datetime.now().date()

    return (
        db.query(Programacion)
        .filter(
            and_(
                Programacion.fecha_programada < hoy,
                Programacion.estado == EstadoProgramacionEnum.PENDIENTE.value
            )
        )
        .order_by(Programacion.fecha_programada)
        .limit(limit)
        .all()
    )


# ============================================================================
# FUNCIONES DE CREACIÓN Y GENERACIÓN AUTOMÁTICA (CREATE)
# ============================================================================

def crear_programacion(
    db: Session,
    programacion_in: ProgramacionCreate
) -> Programacion:
    """
    Crea una nueva programación de mantenimiento.

    Args:
        db (Session): Sesión de SQLAlchemy
        programacion_in (ProgramacionCreate): Datos validados

    Returns:
        Programacion: Registro creado

    Raises:
        ValueError: Si equipo o tipo no existe
        IntegrityError: Si hay error de BD
    """
    try:
        # Validar existencia de equipo
        equipo = db.query(Equipo).filter(
            Equipo.id == programacion_in.equipo_id
        ).first()
        if not equipo:
            raise ValueError(f"Equipo {programacion_in.equipo_id} no existe")

        # Validar existencia de tipo de mantenimiento
        tipo_mant = db.query(TipoMantenimiento).filter(
            TipoMantenimiento.id == programacion_in.tipo_mantenimiento_id
        ).first()
        if not tipo_mant:
            raise ValueError(f"Tipo de mantenimiento {programacion_in.tipo_mantenimiento_id} no existe")

        # Crear programación
        datos = programacion_in.model_dump()
        nueva_programacion = Programacion(**datos)
        db.add(nueva_programacion)
        db.flush()

        from app.services.audit_event_processor import registrar_evento_crud
        registrar_evento_crud(
            db,
            tabla_afectada="programaciones",
            registro_id=nueva_programacion.id,
            encargado_id=programacion_in.encargado_id,
            accion="create",
            valor_nuevo=EstadoProgramacionEnum.PENDIENTE.value,
            equipo_id=programacion_in.equipo_id,
        )

        db.commit()
        db.refresh(nueva_programacion)

        return nueva_programacion

    except IntegrityError as e:
        db.rollback()
        raise IntegrityError(
            statement="Error al crear programación",
            params={"equipo_id": programacion_in.equipo_id},
            orig=e.orig
        ) from e


def generar_proxima_programacion(
    db: Session,
    equipo_id: int,
    tipo_mantenimiento_id: int,
    encargado_id: int,
    mantenimiento_id: Optional[int] = None
) -> Optional[Programacion]:
    """
    ** CRÍTICA PARA LÓGICA OPERACIONAL **

    Genera automáticamente la próxima programación de mantenimiento basada en
    la frecuencia_dias configurada en el tipo_mantenimiento.

    Algoritmo:
    1. Obtiene tipo_mantenimiento y lee frecuencia_dias
    2. Calcula fecha_programada = hoy + frecuencia_dias
    3. Crea nueva Programacion (Pendiente)
    4. Linkea al mantenimiento que ya se completó (auditoría)

    EJEMPLO:
    - Preventivo cada 30 días, ejecutado hoy (5 May)
    - Genera automáticamente próximo: 4 Jun (30 días después)
    - Sistema establece alerta: "Próxima cita el 4 Jun"

    Args:
        db (Session): Sesión de SQLAlchemy
        equipo_id (int): Equipo a mantener
        tipo_mantenimiento_id (int): Tipo (para leer frecuencia)
        encargado_id (int): Técnico asignado a próxima cita
        mantenimiento_id (Optional[int]): FK hacia mantenimiento completado (auditoría)

    Returns:
        Optional[Programacion]: Nueva programación generada, o None si no aplica

    Raises:
        ValueError: Si tipo_mantenimiento no existe o no tiene frecuencia
    """
    try:
        # Obtener tipo de mantenimiento
        tipo_mant = db.query(TipoMantenimiento).filter(
            TipoMantenimiento.id == tipo_mantenimiento_id
        ).first()

        if not tipo_mant:
            raise ValueError(f"Tipo de mantenimiento {tipo_mantenimiento_id} no existe")

        # Si no tiene frecuencia, no genera próxima (ej: inspecciones puntuales)
        if not tipo_mant.frecuencia_dias:
            return None

        # Calcular fecha de próxima programación
        hoy = datetime.now().date()
        fecha_proxima = hoy + timedelta(days=tipo_mant.frecuencia_dias)

        # Crear programación
        nueva_prog = Programacion(
            equipo_id=equipo_id,
            encargado_id=encargado_id,
            tipo_mantenimiento_id=tipo_mantenimiento_id,
            fecha_programada=fecha_proxima,
            estado=EstadoProgramacionEnum.PENDIENTE.value,
            mantenimiento_id=mantenimiento_id,  # Link al que acaba de completarse
            observaciones=f"Generada automáticamente. Próximo {tipo_mant.nombre.lower()} recomendado."
        )

        db.add(nueva_prog)
        db.commit()
        db.refresh(nueva_prog)

        return nueva_prog

    except Exception as e:
        db.rollback()
        raise


# ============================================================================
# FUNCIONES DE ACTUALIZACIÓN (UPDATE)
# ============================================================================

def actualizar_programacion(
    db: Session,
    programacion: Programacion,
    update_in: ProgramacionUpdate
) -> Programacion:
    """
    Actualiza una programación existente.

    Args:
        db (Session): Sesión de SQLAlchemy
        programacion (Programacion): Objeto a actualizar
        update_in (ProgramacionUpdate): Datos a actualizar

    Returns:
        Programacion: Registro actualizado
    """
    try:
        datos = update_in.model_dump(exclude_unset=True)

        for campo, valor in datos.items():
            if valor is not None:
                setattr(programacion, campo, valor)

        db.commit()
        db.refresh(programacion)

        return programacion

    except IntegrityError as e:
        db.rollback()
        raise


def cambiar_estado_programacion(
    db: Session,
    programacion_id: int,
    nuevo_estado: str,
    mantenimiento_id: Optional[int] = None
) -> Optional[Programacion]:
    """
    Cambia el estado de una programación y opcionalmente linkea un mantenimiento.

    Transiciones válidas:
    - Pendiente → Completado (cuando se ejecuta)
    - Pendiente → Cancelado (si se cancela)
    - Pendiente → Vencido (automático si fecha < hoy)

    Args:
        db (Session): Sesión de SQLAlchemy
        programacion_id (int): ID de la programación
        nuevo_estado (str): Nuevo estado
        mantenimiento_id (Optional[int]): Si se completa, linkear mantenimiento

    Returns:
        Optional[Programacion]: Programación actualizada o None si no existe
    """
    programacion = obtener_programacion_por_id(db, programacion_id)
    if not programacion:
        return None

    try:
        programacion.estado = nuevo_estado
        if mantenimiento_id is not None:
            programacion.mantenimiento_id = mantenimiento_id

        db.commit()
        db.refresh(programacion)

        return programacion

    except IntegrityError as e:
        db.rollback()
        raise


# ============================================================================
# FUNCIONES ANALÍTICAS
# ============================================================================

def contar_programaciones_por_estado(db: Session) -> dict:
    """
    Cuenta programaciones agrupadas por estado.

    Útil para resúmenes de dashboard.

    Returns:
        dict: {'Pendiente': count, 'Completado': count, ...}
    """
    resultados = (
        db.query(Programacion.estado, func.count(Programacion.id))
        .group_by(Programacion.estado)
        .all()
    )

    return {estado: count for estado, count in resultados}


def obtener_proximas_programaciones(
    db: Session,
    dias_adelante: int = 7
) -> List[Programacion]:
    """
    Obtiene programaciones dentro de N días (para alertas).

    Útil para email alerts: "Hay 3 mantenimientos programados para esta semana"

    Args:
        db (Session): Sesión de SQLAlchemy
        dias_adelante (int): Horizon en días (default: 7)

    Returns:
        List[Programacion]: Programaciones en el rango de fechas
    """
    hoy = datetime.now().date()
    fecha_limite = hoy + timedelta(days=dias_adelante)

    return (
        db.query(Programacion)
        .filter(
            and_(
                Programacion.fecha_programada.between(hoy, fecha_limite),
                Programacion.estado == EstadoProgramacionEnum.PENDIENTE.value
            )
        )
        .order_by(Programacion.fecha_programada)
        .all()
    )


def cancelar_programacion_con_auditoria(
    db: Session,
    programacion_id: int,
    justificacion: str,
    encargado_id: int,
) -> Optional[Programacion]:
    """
    Cancela una programación registrando un evento de negocio con motivo documentado.

    Regla de negocio: la justificación ya fue validada por Pydantic antes de invocar este servicio.
    """
    programacion = obtener_programacion_por_id(db, programacion_id)
    if not programacion:
        return None

    estado_anterior = programacion.estado

    try:
        programacion.estado = EstadoProgramacionEnum.CANCELADO.value

        procesar_evento_auditoria(
            db,
            EventoAuditoriaCreate(
                tipo_evento=TipoEventoEnum.PROGRAMACION_MANTENIMIENTO,
                encargado_id=encargado_id,
                registro_id=programacion_id,
                tabla_afectada="programaciones",
                campo="cancelacion",
                estado_anterior=estado_anterior,
                estado_nuevo=EstadoProgramacionEnum.CANCELADO.value,
                justificacion=justificacion,
                equipo_id=programacion.equipo_id,
            ),
            flush=True,
        )

        db.commit()
        db.refresh(programacion)
        return programacion

    except IntegrityError:
        db.rollback()
        raise

