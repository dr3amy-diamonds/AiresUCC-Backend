"""
Módulo de Endpoints para Mantenimientos.

Este módulo implementa las rutas CRUD para gestionar mantenimientos de equipos:
- POST /mantenimientos          → Crear nuevo registro de mantenimiento
- GET  /mantenimientos          → Listar paginado con filtros
- GET  /mantenimientos/{id}     → Obtener detalles por ID
- PUT  /mantenimientos/{id}     → Actualizar detalles
- GET /mantenimientos/equipo/{equipo_id}/historial → Historial de un equipo
- GET /mantenimientos/estadisticas/resumen → Estadísticas generales

**Contexto de Negocio (Flujo del Técnico en Terreno):**

El técnico en el terreno completa un trabajo de mantenimiento en un equipo de aire
acondicionado y llena un formulario en el frontend HTML con:
1. ID del equipo mantenido
2. Detalles del trabajo realizado (limpieza, recarga, reparación, etc)
3. Fecha del mantenimiento (hoy por defecto)

LÓGICA CRÍTICA:
- POST /mantenimientos registra el evento y AUTOMÁTICAMENTE:
  * Cambia estado del equipo a "Operativo" (fin de reparación/mantenimiento)
  * Genera la próxima programación automática (si el tipo tiene frecuencia)
  * Crea auditoría histórica inmutable

Arquitectura Limpia:
- Rutas delegan lógica a servicios (app.services.mantenimiento)
- Esquemas Pydantic validan entrada/salida
- Códigos HTTP semánticos: 201 Created, 400 Bad Request, 404 Not Found
- Documentación con ejemplos en Swagger
- Manejo de excepciones robusto (ValueError, IntegrityError, Exception)
"""

from typing import Optional, List
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.session import get_db
from app.schemas.mantenimiento import (
    MantenimientoCreate,
    MantenimientoResponse,
    MantenimientoUpdate,
    MantenimientoListResponse,
    MantenimientoEstadisticas,
)
from app.services import mantenimiento as mantenimiento_service
from app.services import programacion as programacion_service


# ============================================================================
# CONFIGURACIÓN DEL ROUTER
# ============================================================================

router = APIRouter(
    prefix="/mantenimientos",
    tags=["Mantenimientos"],
    responses={
        404: {"description": "Mantenimiento no encontrado"},
        409: {"description": "Conflicto: violación de integridad"},
    },
)


# ============================================================================
# ENDPOINTS CRUD
# ============================================================================

@router.post(
    "/",
    response_model=MantenimientoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nuevo registro de mantenimiento",
    description="""
    Crea un nuevo registro de mantenimiento completado.
    
    **CRÍTICO:** Al registrar cierre, automáticamente cambia estado del equipo a "Operativo".
    
    **Campos requeridos:**
    - equipo_id: ID del equipo mantenido
    - encargado_id: ID del técnico que realizó el mantenimiento
    - tipo_mantenimiento_id: ID del tipo (Preventivo, Correctivo, etc)
    - registrado_por: ID del usuario autenticado que registra
    - fecha_mantenimiento: Fecha del mantenimiento (YYYY-MM-DD)
    
    **Respuesta:**
    - Returns 201 Created con datos del mantenimiento
    - Incluye timestamps y relaciones (equipo, técnico, tipo)
    """,
    responses={
        201: {"description": "Mantenimiento creado exitosamente"},
        400: {"description": "Datos inválidos (validación Pydantic)"},
        404: {"description": "Equipo o técnico no existe"},
        409: {"description": "Error de integridad referencial"},
    },
)
def crear_mantenimiento(
    mantenimiento_in: MantenimientoCreate,
    db: Session = Depends(get_db),
) -> MantenimientoResponse:
    """
    Crear nuevo registro de mantenimiento.

    El registro activa automáticamente la lógica de negocio:
    1. Valida que equipo y técnico existan
    2. Crea registro histórico
    3. Cambia estado del equipo a "Operativo"
    4. Genera siguiente programación (si aplica)
    """
    try:
        # Crear mantenimiento (esto ya cambia estado del equipo)
        nuevo_mantenimiento = mantenimiento_service.crear_mantenimiento(
            db, mantenimiento_in
        )

        # Generar próxima programación automáticamente
        try:
            programacion_service.generar_proxima_programacion(
                db,
                equipo_id=nuevo_mantenimiento.equipo_id,
                tipo_mantenimiento_id=nuevo_mantenimiento.tipo_mantenimiento_id,
                encargado_id=nuevo_mantenimiento.encargado_id,
                mantenimiento_id=nuevo_mantenimiento.id
            )
        except Exception:
            # No bloquear creación si no se puede generar próxima
            # (ej: tipo sin frecuencia)
            pass

        return nuevo_mantenimiento

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Error de integridad: verificar que equipo y técnico existan"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )


@router.get(
    "/",
    response_model=MantenimientoListResponse,
    summary="Listar mantenimientos con filtros",
    description="""
    Obtiene lista paginada de mantenimientos con filtros opcionales.
    
    **Filtros disponibles:**
    - equipo_id: Listar solo mantenimientos de un equipo específico
    - encargado_id: Listar solo mantenimientos de un técnico
    - fecha_desde: Filtrar mantenimientos a partir de fecha
    - fecha_hasta: Filtrar mantenimientos hasta fecha
    - page: Número de página (default: 1)
    - size: Registros por página (default: 10, máximo: 100)
    
    **Ejemplo:**
    `GET /mantenimientos?equipo_id=5&page=1&size=20`
    """,
)
def listar_mantenimientos(
    db: Session = Depends(get_db),
    equipo_id: Optional[int] = Query(None, gt=0, description="Filtrar por equipo"),
    encargado_id: Optional[int] = Query(None, gt=0, description="Filtrar por técnico"),
    fecha_desde: Optional[date] = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha fin (YYYY-MM-DD)"),
    page: int = Query(1, ge=1, description="Página (comienza en 1)"),
    size: int = Query(10, ge=1, le=100, description="Registros por página (máx 100)"),
) -> MantenimientoListResponse:
    """Listar mantenimientos con paginación y filtros."""
    try:
        skip = (page - 1) * size

        mantenimientos, total = mantenimiento_service.listar_mantenimientos(
            db,
            skip=skip,
            limit=size,
            equipo_id=equipo_id,
            encargado_id=encargado_id,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
        )

        return MantenimientoListResponse(
            total=total,
            page=page,
            size=size,
            items=mantenimientos
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al listar mantenimientos: {str(e)}"
        )


@router.get(
    "/{mantenimiento_id}",
    response_model=MantenimientoResponse,
    summary="Obtener detalles de un mantenimiento",
    responses={
        200: {"description": "Mantenimiento encontrado"},
        404: {"description": "Mantenimiento no existe"},
    },
)
def obtener_mantenimiento(
    mantenimiento_id: int = Path(..., gt=0, description="ID del mantenimiento"),
    db: Session = Depends(get_db),
) -> MantenimientoResponse:
    """Obtener detalles completos de un mantenimiento por ID."""
    mantenimiento = mantenimiento_service.obtener_mantenimiento_por_id(
        db, mantenimiento_id
    )

    if not mantenimiento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mantenimiento {mantenimiento_id} no encontrado"
        )

    return mantenimiento


@router.put(
    "/{mantenimiento_id}",
    response_model=MantenimientoResponse,
    summary="Actualizar mantenimiento",
    description="""
    Actualiza un registro de mantenimiento existente.
    
    **Campos actualizables:**
    - detalle_mantenimiento: Descripción del trabajo realizado
    
    **Campos INMUTABLES (auditoría):**
    - equipo_id
    - encargado_id
    - fecha_mantenimiento
    - registrado_por
    """,
)
def actualizar_mantenimiento(
    mantenimiento_id: int = Path(..., gt=0),
    update_in: MantenimientoUpdate = None,
    db: Session = Depends(get_db),
) -> MantenimientoResponse:
    """Actualizar detalles de un mantenimiento."""
    mantenimiento = mantenimiento_service.obtener_mantenimiento_por_id(
        db, mantenimiento_id
    )

    if not mantenimiento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mantenimiento {mantenimiento_id} no encontrado"
        )

    try:
        actualizado = mantenimiento_service.actualizar_mantenimiento(
            db, mantenimiento, update_in
        )
        return actualizado

    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Error de integridad al actualizar"
        )


@router.delete(
    "/{mantenimiento_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar mantenimiento",
    description="""
    Elimina un registro de mantenimiento (CUIDADO: afecta auditoría histórica).
    
    **Usar solo para:**
    - Duplicados accidentales
    - Datos errados ingresados recientemente
    
    **No usar para:**
    - Datos históricos correctos (mante para auditoría)
    """,
)
def eliminar_mantenimiento(
    mantenimiento_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
) -> None:
    """Eliminar un mantenimiento (NO RECOMENDADO - use soft delete en producción)."""
    exito = mantenimiento_service.eliminar_mantenimiento(db, mantenimiento_id)

    if not exito:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mantenimiento {mantenimiento_id} no encontrado"
        )


# ============================================================================
# ENDPOINTS ADICIONALES
# ============================================================================

@router.get(
    "/equipo/{equipo_id}/historial",
    response_model=List[MantenimientoResponse],
    summary="Obtener historial de mantenimientos de un equipo",
    description="""
    Retorna el historial completo de mantenimientos realizados a un equipo específico.
    
    Útil para auditoría y visualizar qué se ha hecho a un aire acondicionado.
    """,
)
def obtener_historial_equipo(
    equipo_id: int = Path(..., gt=0, description="ID del equipo"),
    limit: int = Query(20, ge=1, le=100, description="Máximo registros"),
    db: Session = Depends(get_db),
) -> List[MantenimientoResponse]:
    """Obtener historial de mantenimientos de un equipo."""
    historial = mantenimiento_service.obtener_historial_equipo(
        db, equipo_id, limit=limit
    )

    return historial


@router.get(
    "/estadisticas/resumen",
    response_model=MantenimientoEstadisticas,
    summary="Obtener estadísticas de mantenimiento",
    description="""
    Calcula estadísticas globales de mantenimiento en período reciente.
    
    Útil para dashboards y reportes ejecutivos.
    """,
)
def obtener_estadisticas_mantenimiento(
    db: Session = Depends(get_db),
) -> MantenimientoEstadisticas:
    """Obtener estadísticas generales de mantenimiento."""
    try:
        stats = mantenimiento_service.obtener_estadisticas_mantenimiento(db)

        # Transformar a schema de respuesta
        total_mant = stats["total"]
        por_equipo = stats["por_equipo"]
        por_tecnico = stats["por_tecnico"]

        # Contar preventivos vs correctivos (opcional, si necesita más detalle)
        preventivos = mantenimiento_service.contar_mantenimientos_por_tipo(
            db, tipo_mantenimiento_id=1  # Suponiendo ID 1 = Preventivo
        )
        correctivos = total_mant - preventivos

        return MantenimientoEstadisticas(
            total_mantenimientos=total_mant,
            mantenimientos_preventivos=preventivos,
            mantenimientos_correctivos=correctivos,
            porcentaje_preventivo=round(
                (preventivos / total_mant * 100) if total_mant > 0 else 0,
                2
            ),
            equipos_mantenidos=len(por_equipo),
            promedio_por_equipo=round(
                total_mant / len(por_equipo) if por_equipo else 0,
                2
            )
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al calcular estadísticas: {str(e)}"
        )


"""
INTEGRACIÓN MANUAL EN api.py:

from app.api.v1.endpoints import mantenimientos

router = APIRouter()
router.include_router(mantenimientos.router)

Rutas resultantes:
- POST   /api/v1/mantenimientos
- GET    /api/v1/mantenimientos
- GET    /api/v1/mantenimientos/{id}
- PUT    /api/v1/mantenimientos/{id}
- DELETE /api/v1/mantenimientos/{id}
- GET    /api/v1/mantenimientos/equipo/{equipo_id}/historial
- GET    /api/v1/mantenimientos/estadisticas/resumen
"""

