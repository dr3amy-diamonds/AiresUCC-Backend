"""
Módulo de Endpoints para Mantenimientos.
Maneja el registro de servicios técnicos y la trazabilidad de costos del campus.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.usuario import Usuario
from app.schemas.mantenimiento import (
    MantenimientoCreate,
    MantenimientoResponse,
    MantenimientoEstadisticas,
    CerrarOrdenRequest,
    CerrarOrdenResponse,
)
from app.services import mantenimiento as mantenimiento_service
from app.core.security import require_role, get_current_user

router = APIRouter(prefix="/mantenimientos", tags=["mantenimientos"])

@router.post(
    "/cerrar-orden/{orden_id}",
    response_model=CerrarOrdenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cierre técnico atómico de una orden de programación",
    description="""
    Ejecuta el **triple disparo atómico** en una sola transacción:

    1. INSERT en `mantenimientos` (costo = sumatoria de materiales, sin mano de obra)
    2. UPDATE en `programaciones` (estado → Completado, enlace `mantenimiento_id`)
    3. INSERT en `auditoria` (bitácora valor_anterior → valor_nuevo)

    Si cualquier paso falla, se ejecuta `rollback()` completo.
    """,
)
def cerrar_orden_programacion(
    orden_id: int = Path(..., gt=0, description="ID de la programación (orden de trabajo)"),
    payload: CerrarOrdenRequest = ...,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> CerrarOrdenResponse:
    """Cierra una orden de mantenimiento con transacción atómica."""
    try:
        mantenimiento, programacion, auditoria_count = mantenimiento_service.cerrar_orden_atomica(
            db,
            orden_id=orden_id,
            payload=payload,
            usuario_id=current_user.id,
        )
        return CerrarOrdenResponse(
            mantenimiento=MantenimientoResponse.model_validate(mantenimiento),
            programacion_id=programacion.id,
            programacion_estado=programacion.estado,
            auditoria_registros=auditoria_count,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al cerrar la orden: {str(e)}",
        )

@router.post("/", response_model=MantenimientoResponse, status_code=status.HTTP_201_CREATED)
def crear_mantenimiento(
    mantenimiento_in: MantenimientoCreate,
    db: Session = Depends(get_db)
):
    """
    Registra una nueva intervención técnica.

    LÓGICA DEL MVP:
    1. Guarda el 'costo_servicio' para el análisis financiero.
    2. Al registrarse, el servicio debe actualizar automáticamente
       la 'ultima_fecha' en la tabla de equipos.
    """
    try:
        return mantenimiento_service.crear_mantenimiento(db, mantenimiento_in)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al registrar el mantenimiento: {str(e)}"
        )

@router.get("/", response_model=List[MantenimientoResponse], dependencies=[Depends(require_role("Jefe de Infraestructura", "Auxiliar de Infraestructura", "Tecnico"))])
def listar_mantenimientos(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    equipo_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Consulta el historial de mantenimientos.
    Permite filtrar por un equipo específico para ver su hoja de vida técnica.

    **Roles Permitidos:** Jefe de Infraestructura, Auxiliar de Infraestructura, Tecnico

    **Parámetros:**
    - skip: Número de registros a saltar (default: 0)
    - limit: Máximo de registros a retornar (default: 10, máximo: 100)
    - equipo_id: Filtrar historial de un equipo específico (opcional)
    """
    mantenimientos, _total = mantenimiento_service.listar_mantenimientos(
        db, skip=skip, limit=limit, equipo_id=equipo_id
    )
    return mantenimientos

@router.get("/{mantenimiento_id}", response_model=MantenimientoResponse, dependencies=[Depends(require_role("Jefe de Infraestructura", "Auxiliar de Infraestructura", "Tecnico"))])
def leer_mantenimiento(mantenimiento_id: int, db: Session = Depends(get_db)):
    """
    Obtiene los detalles de una intervención específica.

    **Roles Permitidos:** Jefe de Infraestructura, Auxiliar de Infraestructura, Tecnico
    """
    db_mantenimiento = mantenimiento_service.obtener_mantenimiento_por_id(db, mantenimiento_id)
    if not db_mantenimiento:
        raise HTTPException(status_code=404, detail="Registro de mantenimiento no encontrado")
    return db_mantenimiento

@router.get("/estadisticas/resumen", response_model=MantenimientoEstadisticas)
def obtener_resumen_estadistico(db: Session = Depends(get_db)):
    """
    Endpoint para el Dashboard.
    Calcula KPIs como el porcentaje de preventivos vs correctivos y el gasto total.
    """
    try:
        return mantenimiento_service.obtener_estadisticas_resumen(db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al calcular estadísticas: {str(e)}"
        )