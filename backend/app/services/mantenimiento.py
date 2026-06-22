"""
Capa de Servicios para la Entidad Mantenimiento.

Este módulo encapsula toda la lógica de negocio relacionada con mantenimientos:
- Creación de registros con validación de FK
- Listado paginado con filtros
- ** CRÍTICO: Al crear, cambia estado del equipo a "Operativo" **
- Actualización con auditoría
- Búsquedas por equipo, técnico, fecha

Arquitectura:
- Lógica de negocio separada de rutas FastAPI
- Validación de integridad referencial
- Excepciones lanzadas para que endpoints manejen
- Timestamps de BD (no cliente)

NOTA MUY IMPORTANTE:
El campo 'registrado_por' debe ser inyectado desde JWT del usuario autenticado.
"""

from typing import Optional, List, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, desc

from app.models.mantenimiento import Mantenimiento
from app.models.programacion import Programacion
from app.models.equipo import Equipo
from app.models.usuario import Usuario
from app.models.componente_usado import ComponenteUsado
from app.models.tipo_componente import TipoComponente
from app.schemas.mantenimiento import (
    MantenimientoCreate,
    MantenimientoUpdate,
    CerrarOrdenRequest,
    ComponenteUsadoInput,
)
from app.schemas.programacion import EstadoProgramacionEnum
from app.schemas.auditoria import EventoAuditoriaCreate, TipoEventoEnum
from app.services.audit_event_processor import procesar_evento_auditoria


def _persistir_componentes_mantenimiento(
    db: Session,
    mantenimiento_id: int,
    componentes: List[ComponenteUsadoInput],
) -> None:
    """Registra insumos fijos y adicionales en componentes_usados."""
    for item in componentes:
        if item.repuesto_utilizado_id:
            repuesto_id = item.repuesto_utilizado_id
        else:
            nombre = (item.nombre or "").strip()
            existente = (
                db.query(TipoComponente)
                .filter(TipoComponente.nombre == nombre)
                .first()
            )
            if existente:
                repuesto_id = existente.id
            else:
                nuevo_tipo = TipoComponente(nombre=nombre)
                db.add(nuevo_tipo)
                db.flush()
                repuesto_id = nuevo_tipo.id

        db.add(
            ComponenteUsado(
                cantidad=Decimal(str(item.cantidad)),
                precio_unitario=Decimal(str(item.precio_unitario)),
                mantenimiento_realizado_id=mantenimiento_id,
                repuesto_utilizado_id=repuesto_id,
            )
        )


# ============================================================================
# FUNCIONES DE LECTURA (READ)
# ============================================================================

def obtener_mantenimiento_por_id(db: Session, mantenimiento_id: int) -> Optional[Mantenimiento]:
    """
    Obtiene un registro de mantenimiento por su ID.

    Args:
        db (Session): Sesión de SQLAlchemy
        mantenimiento_id (int): ID del mantenimiento a buscar

    Returns:
        Optional[Mantenimiento]: Objeto encontrado o None

    Ejemplo:
        >>> mant = obtener_mantenimiento_por_id(db, 42)
        >>> if mant:
        ...     print(f"Mantenimiento del equipo {mant.equipo.codigo_activo}")
    """
    return db.query(Mantenimiento).filter(
        Mantenimiento.id == mantenimiento_id
    ).first()


def listar_mantenimientos(
    db: Session,
    skip: int = 0,
    limit: int = 10,
    equipo_id: Optional[int] = None,
    encargado_id: Optional[int] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
) -> Tuple[List[Mantenimiento], int]:
    """
    Obtiene lista paginada de mantenimientos con filtros opcionales.

    Args:
        db (Session): Sesión de SQLAlchemy
        skip (int): Offset para paginación
        limit (int): Límite de registros (máximo 100)
        equipo_id (Optional[int]): Filtrar por equipo específico
        encargado_id (Optional[int]): Filtrar por técnico responsable
        fecha_desde (Optional[date]): Filtrar mantenimientos a partir de fecha
        fecha_hasta (Optional[date]): Filtrar mantenimientos hasta fecha

    Returns:
        Tuple[List[Mantenimiento], int]: (lista de mantenimientos, total)

    Ejemplo:
        >>> mantenimientos, total = listar_mantenimientos(
        ...     db,
        ...     equipo_id=5,
        ...     fecha_desde=date(2026, 1, 1),
        ...     limit=20
        ... )
        >>> print(f"Mostrando {len(mantenimientos)} de {total} mantenimientos")
    """
    # Construir query base
    query = db.query(Mantenimiento)

    # Aplicar filtros
    if equipo_id is not None:
        query = query.filter(Mantenimiento.equipo_id == equipo_id)

    if encargado_id is not None:
        query = query.filter(Mantenimiento.encargado_id == encargado_id)

    if fecha_desde is not None:
        query = query.filter(Mantenimiento.fecha_mantenimiento >= fecha_desde)

    if fecha_hasta is not None:
        query = query.filter(Mantenimiento.fecha_mantenimiento <= fecha_hasta)

    # Contar total antes de paginar
    total = query.count()

    # Paginar y ordenar (más recientes primero)
    mantenimientos = (
        query
        .order_by(desc(Mantenimiento.fecha_mantenimiento))
        .offset(skip)
        .limit(min(limit, 100))  # Cap limit a 100
        .all()
    )

    return mantenimientos, total


def obtener_historial_equipo(
    db: Session,
    equipo_id: int,
    limit: int = 10
) -> List[Mantenimiento]:
    """
    Obtiene el historial de mantenimientos de un equipo específico.

    Useful para auditoría y visualizar qué se ha hecho a un aire.

    Args:
        db (Session): Sesión de SQLAlchemy
        equipo_id (int): ID del equipo
        limit (int): Máximo de registros a retornar

    Returns:
        List[Mantenimiento]: Historial ordenado por fecha descendente

    Ejemplo:
        >>> historial = obtener_historial_equipo(db, equipo_id=5, limit=20)
        >>> for mant in historial:
        ...     print(f"{mant.fecha_mantenimiento}: {mant.detalle_mantenimiento}")
    """
    return (
        db.query(Mantenimiento)
        .filter(Mantenimiento.equipo_id == equipo_id)
        .order_by(desc(Mantenimiento.fecha_mantenimiento))
        .limit(limit)
        .all()
    )


def contar_mantenimientos_por_tipo(
    db: Session,
    tipo_mantenimiento_id: int,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None
) -> int:
    """
    Cuenta mantenimientos de un tipo específico en rango de fechas.

    Útil para estadísticas (cuántos preventivos vs correctivos).

    Args:
        db (Session): Sesión de SQLAlchemy
        tipo_mantenimiento_id (int): ID del tipo de mantenimiento
        fecha_desde (Optional[date]): Fecha inicio (default: 30 días atrás)
        fecha_hasta (Optional[date]): Fecha fin (default: hoy)

    Returns:
        int: Cantidad de mantenimientos
    """
    # Default: últimos 30 días
    if fecha_desde is None:
        fecha_desde = datetime.now().date() - timedelta(days=30)
    if fecha_hasta is None:
        fecha_hasta = datetime.now().date()

    return (
        db.query(func.count(Mantenimiento.id))
        .filter(Mantenimiento.tipo_mantenimiento_id == tipo_mantenimiento_id)
        .filter(Mantenimiento.fecha_mantenimiento.between(fecha_desde, fecha_hasta))
        .scalar() or 0
    )


# ============================================================================
# FUNCIONES DE CREACIÓN (CREATE) - CRÍTICA PARA LÓGICA DE NEGOCIO
# ============================================================================

def crear_mantenimiento(
    db: Session,
    mantenimiento_in: MantenimientoCreate
) -> Mantenimiento:
    """
    Crea un nuevo registro de mantenimiento en la BD.

    ** CRÍTICO: LÓGICA DE NEGOCIO PRINCIPAL **

    Flujo Completo:
    1. Validar que equipo existe
    2. Crear registro de mantenimiento (con costo_servicio)
    3. Actualizar fechas de mantenimiento del equipo (ultima_fecha y proxima_fecha)
    4. Cambiar estado del equipo a "Operativo" (fin de reparación)
    5. Persistir cambios atómicamente

    Args:
        db (Session): Sesión de SQLAlchemy con transacción activa
        mantenimiento_in (MantenimientoCreate): Datos validados de Pydantic

    Returns:
        Mantenimiento: Registro creado con ID y timestamps

    Raises:
        ValueError: Si equipo_id no existe
        IntegrityError: Si hay error de integridad en BD

    Ejemplo:
        >>> from app.schemas.mantenimiento import MantenimientoCreate
        >>> from datetime import date
        >>> mant_in = MantenimientoCreate(
        ...     equipo_id=5,
        ...     encargado_id=3,
        ...     tipo_mantenimiento_id=1,
        ...     registrado_por=3,
        ...     detalle_mantenimiento="Limpieza de filtros y recarga de refrigerante",
        ...     costo_servicio=Decimal('150.00'),
        ...     fecha_mantenimiento=date.today()
        ... )
        >>> nuevo_mant = crear_mantenimiento(db, mant_in)
        >>> print(f"Mantenimiento creado: ID {nuevo_mant.id}")
    """
    try:
        # 1. VALIDAR EXISTENCIA DEL EQUIPO
        equipo = db.query(Equipo).filter(Equipo.id == mantenimiento_in.equipo_id).first()
        if not equipo:
            raise ValueError(f"Equipo con ID {mantenimiento_in.equipo_id} no existe")

        # 2. CREAR REGISTRO DE MANTENIMIENTO (incluye costo_mano_obra)
        datos = mantenimiento_in.model_dump()
        nuevo_mantenimiento = Mantenimiento(**datos)
        db.add(nuevo_mantenimiento)

        # 3. ** AUTOMATIZACIÓN CRÍTICA DE FECHAS **
        # Actualiza las fechas del equipo después de mantenimiento
        # Usa la fecha del registro de mantenimiento, no la fecha actual del sistema
        equipo.ultima_fecha = mantenimiento_in.fecha_mantenimiento
        equipo.proxima_fecha = mantenimiento_in.fecha_mantenimiento + timedelta(days=90)

        # 4. ** CAMBIAR ESTADO DEL EQUIPO A "OPERATIVO" **
        # NOTA: Esta es la lógica crítica de negocio
        # Si estaba "En reparación" o "Inactivo", pasa a "Operativo"
        # Registra en auditoría que fue mantenido
        equipo.estado = "Operativo"
        equipo.updated_at = datetime.now()

        # 5. PERSISTIR CAMBIOS DE MANERA ATÓMICA
        db.commit()
        db.refresh(nuevo_mantenimiento)

        return nuevo_mantenimiento

    except IntegrityError as e:
        db.rollback()
        raise IntegrityError(
            statement="Error al crear mantenimiento",
            params={"equipo_id": mantenimiento_in.equipo_id},
            orig=e.orig
        ) from e
    except Exception as e:
        db.rollback()
        raise


def cerrar_orden_atomica(
    db: Session,
    orden_id: int,
    payload: CerrarOrdenRequest,
    usuario_id: int,
) -> Tuple[Mantenimiento, Programacion, int]:
    """
    Cierre técnico atómico: mantenimiento + programación + auditoría en un solo commit.

    Pasos (sin commit intermedio):
    1. INSERT mantenimientos (costo = materiales, sin mano de obra)
    2. UPDATE programaciones → Completado + mantenimiento_id
    3. INSERT auditoria (estado y mantenimiento_id)

    Raises:
        ValueError: Orden inexistente, ya cerrada o técnico no asignado
        IntegrityError: Violación de integridad referencial
    """
    programacion = (
        db.query(Programacion)
        .filter(Programacion.id == orden_id)
        .first()
    )
    if not programacion:
        raise ValueError(f"Orden de programación {orden_id} no encontrada")

    if programacion.estado in (
        EstadoProgramacionEnum.COMPLETADO.value,
        EstadoProgramacionEnum.CANCELADO.value,
    ):
        raise ValueError(
            f"La orden {orden_id} ya está en estado '{programacion.estado}' y no admite modificaciones"
        )

    if programacion.encargado_id != usuario_id:
        raise ValueError("Solo el técnico asignado puede cerrar esta orden")

    equipo = db.query(Equipo).filter(Equipo.id == programacion.equipo_id).first()
    if not equipo:
        raise ValueError(f"Equipo {programacion.equipo_id} asociado a la orden no existe")

    estado_anterior = programacion.estado

    try:
        nuevo_mantenimiento = Mantenimiento(
            fecha_mantenimiento=payload.fecha_mantenimiento,
            detalle_mantenimiento=payload.detalle_mantenimiento,
            costo_servicio=Decimal(str(payload.costo_servicio)),
            equipo_id=programacion.equipo_id,
            encargado_id=programacion.encargado_id,
            tipo_mantenimiento_id=programacion.tipo_mantenimiento_id,
            registrado_por=usuario_id,
        )
        db.add(nuevo_mantenimiento)
        db.flush()

        if payload.componentes:
            _persistir_componentes_mantenimiento(
                db, nuevo_mantenimiento.id, payload.componentes
            )

        programacion.estado = EstadoProgramacionEnum.COMPLETADO.value
        programacion.mantenimiento_id = nuevo_mantenimiento.id

        equipo.ultima_fecha = payload.fecha_mantenimiento
        equipo.proxima_fecha = payload.fecha_mantenimiento + timedelta(days=90)
        equipo.estado = "Operativo"
        equipo.updated_at = datetime.now()

        detalle_operativo = (
            f"Se registró el mantenimiento #{nuevo_mantenimiento.id} "
            f"con costo de materiales ${payload.costo_servicio:,.0f} COP."
        )
        procesar_evento_auditoria(
            db,
            EventoAuditoriaCreate(
                tipo_evento=TipoEventoEnum.PROGRAMACION_MANTENIMIENTO,
                encargado_id=usuario_id,
                registro_id=orden_id,
                tabla_afectada="programaciones",
                campo="cierre_orden",
                estado_anterior=estado_anterior,
                estado_nuevo=EstadoProgramacionEnum.COMPLETADO.value,
                equipo_id=programacion.equipo_id,
                detalle_operativo=detalle_operativo,
                mantenimiento_id=nuevo_mantenimiento.id,
            ),
            flush=True,
        )

        db.commit()
        db.refresh(nuevo_mantenimiento)
        db.refresh(programacion)

        return nuevo_mantenimiento, programacion, 1

    except IntegrityError as e:
        db.rollback()
        raise IntegrityError(
            statement="Error al cerrar la orden de forma atómica",
            params={"orden_id": orden_id},
            orig=e.orig,
        ) from e
    except Exception:
        db.rollback()
        raise


# ============================================================================
# FUNCIONES DE ACTUALIZACIÓN (UPDATE)
# ============================================================================

def actualizar_mantenimiento(
    db: Session,
    mantenimiento: Mantenimiento,
    update_in: MantenimientoUpdate
) -> Mantenimiento:
    """
    Actualiza un registro de mantenimiento existente.

    IMPORTANTE:
    - NO se puede cambiar equipo_id (auditoría)
    - NO se puede cambiar fecha (auditoría)
    - Solo se actualiza: detalle_mantenimiento

    Args:
        db (Session): Sesión de SQLAlchemy
        mantenimiento (Mantenimiento): Objeto a actualizar
        update_in (MantenimientoUpdate): Datos a actualizar

    Returns:
        Mantenimiento: Registro actualizado

    Raises:
        IntegrityError: Si hay error de integridad
    """
    try:
        datos = update_in.model_dump(exclude_unset=True)

        for campo, valor in datos.items():
            if valor is not None:
                setattr(mantenimiento, campo, valor)

        db.commit()
        db.refresh(mantenimiento)

        return mantenimiento

    except IntegrityError as e:
        db.rollback()
        raise IntegrityError(
            statement="Error al actualizar mantenimiento",
            params={"mantenimiento_id": mantenimiento.id},
            orig=e.orig
        ) from e


# ============================================================================
# FUNCIONES DE ELIMINACIÓN (DELETE)
# ============================================================================

def eliminar_mantenimiento(db: Session, mantenimiento_id: int) -> bool:
    """
    Elimina un registro de mantenimiento (CUIDADO: auditoría).

    NOTA: Solo debe llamarse en casos especiales (datos duplicados).
    Generalmente debe mantenerse para auditoría histórica.

    Args:
        db (Session): Sesión de SQLAlchemy
        mantenimiento_id (int): ID del mantenimiento a eliminar

    Returns:
        bool: True si se eliminó, False si no existía
    """
    mantenimiento = obtener_mantenimiento_por_id(db, mantenimiento_id)

    if not mantenimiento:
        return False

    try:
        db.delete(mantenimiento)
        db.commit()
        return True
    except IntegrityError as e:
        db.rollback()
        # Si hay FK dependientes, no se puede eliminar
        raise IntegrityError(
            statement="No se puede eliminar mantenimiento con dependencias",
            params={"mantenimiento_id": mantenimiento_id},
            orig=e.orig
        ) from e


# ============================================================================
# FUNCIONES ANALÍTICAS
# ============================================================================

def obtener_estadisticas_mantenimiento(
    db: Session,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None
) -> dict:
    """
    Calcula estadísticas globales de mantenimiento.

    Útil para dashboards y reportes ejecutivos.

    Args:
        db (Session): Sesión de SQLAlchemy
        fecha_desde (Optional[date]): Fecha inicio (default: 30 días atrás)
        fecha_hasta (Optional[date]): Fecha fin (default: hoy)

    Returns:
        dict: Diccionario con estadísticas:
            - total: Total de mantenimientos
            - por_equipo: Diccionario {equipo_id: count}
            - por_tecnico: Diccionario {tecnico_id: count}
            - promedio_por_dia: float
    """
    if fecha_desde is None:
        fecha_desde = datetime.now().date() - timedelta(days=30)
    if fecha_hasta is None:
        fecha_hasta = datetime.now().date()

    # Total de mantenimientos
    total = (
        db.query(func.count(Mantenimiento.id))
        .filter(Mantenimiento.fecha_mantenimiento.between(fecha_desde, fecha_hasta))
        .scalar() or 0
    )

    # Por equipo
    por_equipo = {}
    resultados_equipo = (
        db.query(Mantenimiento.equipo_id, func.count(Mantenimiento.id))
        .filter(Mantenimiento.fecha_mantenimiento.between(fecha_desde, fecha_hasta))
        .group_by(Mantenimiento.equipo_id)
        .all()
    )
    por_equipo = {equipo_id: count for equipo_id, count in resultados_equipo}

    # Por técnico
    por_tecnico = {}
    resultados_tecnico = (
        db.query(Mantenimiento.encargado_id, func.count(Mantenimiento.id))
        .filter(Mantenimiento.fecha_mantenimiento.between(fecha_desde, fecha_hasta))
        .group_by(Mantenimiento.encargado_id)
        .all()
    )
    por_tecnico = {tecnico_id: count for tecnico_id, count in resultados_tecnico}

    # Promedio por día
    dias = (fecha_hasta - fecha_desde).days + 1
    promedio_por_dia = round(total / dias, 2) if dias > 0 else 0

    return {
        "total": total,
        "por_equipo": por_equipo,
        "por_tecnico": por_tecnico,
        "promedio_por_dia": promedio_por_dia,
        "fecha_desde": fecha_desde,
        "fecha_hasta": fecha_hasta,
    }

