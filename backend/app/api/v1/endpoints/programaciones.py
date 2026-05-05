"""
Módulo de Endpoints para Programación de Mantenimiento.

Este módulo implementa rutas REST para la agenda de mantenimientos:
- GET  /programaciones                → Listar con filtros por estado
- POST /programaciones                → Crear nueva programación
- GET  /programaciones/{id}           → Obtener detalles
- PUT  /programaciones/{id}           → Actualizar
- DELETE /programaciones/{id}         → Eliminar
- GET  /programaciones/estado/vencidas → Listing pendientes que están vencidas
- GET  /programaciones/estado/pendientes → Listar próximas
- PUT  /programaciones/{id}/completar → Cambiar estado a Completado

Arquitectura:
- Estados claro: Pendiente, Completado, Cancelado, Vencido
- Alertas automáticas para vencidas
- Linkeo con mantenimientos completados
- Documentación con ejemplos
"""

from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.session import get_db
from app.schemas.programacion import (
    ProgramacionCreate,
    ProgramacionResponse,
    ProgramacionUpdate,
    ProgramacionListResponse,
    EstadoProgramacionEnum,
    ProgramacionesPorEstado,
    ProgramacionResumenAnalytica,
)
from app.services import programacion as programacion_service
from app.services import mantenimiento as mantenimiento_service


# ============================================================================
# CONFIGURACIÓN DEL ROUTER
# ============================================================================

router = APIRouter(
    prefix="/programaciones",
    tags=["Programaciones"],
    responses={
        404: {"description": "Programación no encontrada"},
        409: {"description": "Conflicto: violación de integridad"},
    },
)


# ============================================================================
# ENDPOINTS CRUD
# ============================================================================

@router.post(
    "/",
    response_model=ProgramacionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nueva programación de mantenimiento",
    description="""
    Crea una nueva programación (cita futura) de mantenimiento.
    
    **Campos requeridos:**
    - equipo_id: Aire a mantener
    - encargado_id: Técnico asignado
    - tipo_mantenimiento_id: Tipo (Preventivo, Correctivo, etc)
    - fecha_programada: Cuándo hacer el mantenimiento (debe ser hoy o posterior)
    
    **Flujo típico:**
    1. Admin crea programación manual
    2. Sistema genera automáticamente próximas (después de completar una)
    3. Técnico ve agenda y ejecuta
    4. Al ejecutar, se registra en Mantenimiento (no en Programación)
    """,
)
def crear_programacion(
    programacion_in: ProgramacionCreate,
    db: Session = Depends(get_db),
) -> ProgramacionResponse:
    """Crear nueva programación de mantenimiento."""
    try:
        nueva_prog = programacion_service.crear_programacion(db, programacion_in)
        return nueva_prog

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Error de integridad: verificar que equipo y tipo existan"
        )


@router.get(
    "/",
    response_model=ProgramacionListResponse,
    summary="Listar programaciones con filtros",
    description="""
    Obtiene lista paginada de programaciones con filtros opcionales.
    
    **Filtros disponibles:**
    - estado: Pendiente, Completado, Cancelado, Vencido
    - equipo_id: Listar solo de un equipo específico
    - encargado_id: Listar solo de un técnico
    - vencidas: Si True, muestra solo Pendientes que están atrasadas
    - page: Número de página (default: 1)
    - size: Registros por página (default: 10)
    
    **Ejemplos:**
    - GET /programaciones?estado=Pendiente        → Próximas a hacer
    - GET /programaciones?vencidas=true           → ALERTAS (atrasadas)
    - GET /programaciones?equipo_id=5&estado=Completado → Historial
    """,
)
def listar_programaciones(
    db: Session = Depends(get_db),
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    equipo_id: Optional[int] = Query(None, gt=0, description="Filtrar por equipo"),
    encargado_id: Optional[int] = Query(None, gt=0, description="Filtrar por técnico"),
    vencidas: bool = Query(False, description="Mostrar solo vencidas (Pendiente + fecha < hoy)"),
    page: int = Query(1, ge=1, description="Número de página"),
    size: int = Query(10, ge=1, le=100, description="Registros por página"),
) -> ProgramacionListResponse:
    """Listar programaciones con paginación y filtros."""
    try:
        skip = (page - 1) * size

        programaciones, total, pendientes_vencidas = programacion_service.listar_programaciones(
            db,
            skip=skip,
            limit=size,
            estado=estado,
            equipo_id=equipo_id,
            encargado_id=encargado_id,
            solo_vencidas=vencidas,
        )

        return ProgramacionListResponse(
            total=total,
            page=page,
            size=size,
            pendientes=total if estado == "Pendiente" else pendientes_vencidas,
            vencidas=pendientes_vencidas,
            items=programaciones
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/{programacion_id}",
    response_model=ProgramacionResponse,
    summary="Obtener detalles de una programación",
)
def obtener_programacion(
    programacion_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
) -> ProgramacionResponse:
    """Obtener detalles completos de una programación."""
    prog = programacion_service.obtener_programacion_por_id(db, programacion_id)

    if not prog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Programación {programacion_id} no encontrada"
        )

    return prog


@router.put(
    "/{programacion_id}",
    response_model=ProgramacionResponse,
    summary="Actualizar programación",
)
def actualizar_programacion(
    programacion_id: int = Path(..., gt=0),
    update_in: ProgramacionUpdate = None,
    db: Session = Depends(get_db),
) -> ProgramacionResponse:
    """Actualizar detalles de una programación."""
    prog = programacion_service.obtener_programacion_por_id(db, programacion_id)

    if not prog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Programación {programacion_id} no encontrada"
        )

    try:
        actualizado = programacion_service.actualizar_programacion(
            db, prog, update_in
        )
        return actualizado

    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Error de integridad al actualizar"
        )


@router.delete(
    "/{programacion_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar programación",
)
def eliminar_programacion(
    programacion_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
) -> None:
    """Eliminar una programación (cancelar cita)."""
    prog = programacion_service.obtener_programacion_por_id(db, programacion_id)

    if not prog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Programación {programacion_id} no encontrada"
        )

    # En vez de eliminar, cambiar a "Cancelado"
    prog_cancelada = programacion_service.cambiar_estado_programacion(
        db,
        programacion_id,
        EstadoProgramacionEnum.CANCELADO.value
    )


# ============================================================================
# ENDPOINTS ESPECIALIZADOS POR ESTADO
# ============================================================================

@router.get(
    "/estado/pendientes",
    response_model=ProgramacionListResponse,
    summary="Listar programaciones pendientes",
    description="""
    Obtiene SOLO las programaciones pendientes de ejecutar.
    
    Ordenadas por fecha (próximas primero).
    
    ** Esta es la agenda del técnico para el mes próximo.
    """,
)
def obtener_pendientes(
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
) -> ProgramacionListResponse:
    """Obtener programaciones pendientes (agenda)."""
    try:
        pendientes = programacion_service.obtener_programaciones_por_estado(
            db, EstadoProgramacionEnum.PENDIENTE.value, limit=limit
        )

        return ProgramacionListResponse(
            total=len(pendientes),
            page=1,
            size=limit,
            pendientes=len(pendientes),
            vencidas=0,
            items=pendientes
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/estado/vencidas",
    response_model=ProgramacionListResponse,
    summary="Listar programaciones VENCIDAS (ALERTAS CRÍTICAS)",
    description="""
    ** CRÍTICO PARA ALERTAS **
    
    Obtiene programaciones pendientes que YA PASÓ LA FECHA.
    
    Estos son mantenimientos ATRASADOS que requieren atención inmediata.
    
    El Jefe de Infraestructura debe recibir email notificando estas.
    
    **Interpretación:**
    - 0 vencidas: ExcelentE - cronograma bajo control
    - 1-3 vencidas: GOOD - margen pequeño de error
    - 4+ vencidas: CRÍTICO - sistema desbordado
    """,
)
def obtener_vencidas(
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> ProgramacionListResponse:
    """Obtener programaciones vencidas (mantenimientos atrasados)."""
    try:
        vencidas = programacion_service.obtener_programaciones_vencidas(
            db, limit=limit
        )

        return ProgramacionListResponse(
            total=len(vencidas),
            page=1,
            size=limit,
            pendientes=0,
            vencidas=len(vencidas),
            items=vencidas
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/estado/completadas",
    response_model=ProgramacionListResponse,
    summary="Listar programaciones completadas",
    description="Historial de programaciones que se ejecutaron.",
)
def obtener_completadas(
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
) -> ProgramacionListResponse:
    """Obtener programaciones completadas."""
    try:
        completadas = programacion_service.obtener_programaciones_por_estado(
            db, EstadoProgramacionEnum.COMPLETADO.value, limit=limit
        )

        return ProgramacionListResponse(
            total=len(completadas),
            page=1,
            size=limit,
            pendientes=0,
            vencidas=0,
            items=completadas
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ============================================================================
# ENDPOINTS DE ACCIÓN
# ============================================================================

@router.put(
    "/{programacion_id}/completar",
    response_model=ProgramacionResponse,
    summary="Marcar programación como completada",
    description="""
    Marca una programación como COMPLETADA.
    
    Esto vincula el mantenimiento realizado con la programación.
    
    **Proceso:**
    1. Técnico ejecuta mantenimiento y registra en app
    2. Se crea Mantenimiento (con cambio de estado del equipo)
    3. Se marca Programación como Completada
    4. Sistema genera automáticamente PRÓXIMA programación
    
    **Parámetro:**
    - mantenimiento_id: ID del mantenimiento creado (opcional, puede omitirse)
    """,
)
def completar_programacion(
    programacion_id: int = Path(..., gt=0),
    mantenimiento_id: Optional[int] = Query(None, description="ID del mantenimiento realizado"),
    db: Session = Depends(get_db),
) -> ProgramacionResponse:
    """Marcar una programación como completada."""
    prog = programacion_service.obtener_programacion_por_id(db, programacion_id)

    if not prog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Programación {programacion_id} no encontrada"
        )

    try:
        completada = programacion_service.cambiar_estado_programacion(
            db,
            programacion_id,
            EstadoProgramacionEnum.COMPLETADO.value,
            mantenimiento_id=mantenimiento_id
        )

        # Generar próxima automáticamente
        try:
            programacion_service.generar_proxima_programacion(
                db,
                equipo_id=prog.equipo_id,
                tipo_mantenimiento_id=prog.tipo_mantenimiento_id,
                encargado_id=prog.encargado_id,
                mantenimiento_id=mantenimiento_id
            )
        except Exception:
            # No bloquear si no se puede generar próxima
            pass

        return completada

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put(
    "/{programacion_id}/cancelar",
    response_model=ProgramacionResponse,
    summary="Cancelar programación",
)
def cancelar_programacion(
    programacion_id: int = Path(..., gt=0),
    razon: Optional[str] = Query(None, max_length=200, description="Razón de la cancelación"),
    db: Session = Depends(get_db),
) -> ProgramacionResponse:
    """Cancelar una programación."""
    prog = programacion_service.obtener_programacion_por_id(db, programacion_id)

    if not prog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Programación {programacion_id} no encontrada"
        )

    try:
        cancelada = programacion_service.cambiar_estado_programacion(
            db,
            programacion_id,
            EstadoProgramacionEnum.CANCELADO.value
        )

        # Actualizar observaciones con razón
        if razon:
            cancelada.observaciones = f"Cancelada: {razon}"
            db.commit()
            db.refresh(cancelada)

        return cancelada

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ============================================================================
# ENDPOINTS ANALÍTICOS
# ============================================================================

@router.get(
    "/analisis/agrupar-por-estado",
    response_model=ProgramacionesPorEstado,
    summary="Agrupar programaciones por estado",
    description="""
    Retorna programaciones agrupadas por estado.
    
    Útil para dashboards que necesitan ver distribución de estados.
    """,
)
def agrupar_por_estado(
    db: Session = Depends(get_db),
) -> ProgramacionesPorEstado:
    """Agrupar programaciones por estado."""
    try:
        pendientes = programacion_service.obtener_programaciones_por_estado(
            db, EstadoProgramacionEnum.PENDIENTE.value, limit=1000
        )
        completadas = programacion_service.obtener_programaciones_por_estado(
            db, EstadoProgramacionEnum.COMPLETADO.value, limit=1000
        )
        canceladas = programacion_service.obtener_programaciones_por_estado(
            db, EstadoProgramacionEnum.CANCELADO.value, limit=1000
        )
        vencidas = programacion_service.obtener_programaciones_vencidas(
            db, limit=1000
        )

        return ProgramacionesPorEstado(
            pendientes=pendientes,
            completadas=completadas,
            canceladas=canceladas,
            vencidas=vencidas
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/analisis/resumen",
    response_model=ProgramacionResumenAnalytica,
    summary="Resumen de analítica de programaciones",
)
def obtener_resumen_analisis(
    db: Session = Depends(get_db),
) -> ProgramacionResumenAnalytica:
    """Obtener resumen analítico de programaciones."""
    try:
        conteos = programacion_service.contar_programaciones_por_estado(db)
        proximas = programacion_service.obtener_proximas_programaciones(
            db, dias_adelante=7
        )
        vencidas = programacion_service.obtener_programaciones_vencidas(db, limit=1)

        total = sum(conteos.values())

        return ProgramacionResumenAnalytica(
            total_programaciones=total,
            programaciones_pendientes=conteos.get("Pendiente", 0),
            programaciones_vencidas=len(vencidas),
            porcentaje_cumplimiento=round(
                (conteos.get("Completado", 0) / total * 100) if total > 0 else 0,
                2
            ),
            proxima_fecha_programada=proximas[0].fecha_programada if proximas else None,
            equipo_mas_frecuente=None  # Extensible
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


"""
INTEGRACIÓN MANUAL EN api.py:

from app.api.v1.endpoints import programaciones

router = APIRouter()
router.include_router(programaciones.router)

Rutas resultantes:
- POST   /api/v1/programaciones
- GET    /api/v1/programaciones
- GET    /api/v1/programaciones/{id}
- PUT    /api/v1/programaciones/{id}
- DELETE /api/v1/programaciones/{id}
- GET    /api/v1/programaciones/estado/pendientes
- GET    /api/v1/programaciones/estado/vencidas    ⚠️ ALERTAS CRÍTICAS
- GET    /api/v1/programaciones/estado/completadas
- PUT    /api/v1/programaciones/{id}/completar
- PUT    /api/v1/programaciones/{id}/cancelar
- GET    /api/v1/programaciones/analisis/agrupar-por-estado
- GET    /api/v1/programaciones/analisis/resumen

FLUJO TÍPICO EN UI:

1. Admin crea programación
2. Técnico ve: GET /programaciones/estado/pendientes
3. Técnico ejecuta y registra mantenimiento
4. Sistema marca: PUT /programaciones/{id}/completar
5. Dashboard muestra: GET /programaciones/analisis/resumen
6. Alertas: GET /programaciones/estado/vencidas (si > 0, email a jefe)
"""

