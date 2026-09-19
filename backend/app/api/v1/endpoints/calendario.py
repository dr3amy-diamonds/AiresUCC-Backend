"""
Endpoint de agregación para el Resumen Anual (/calendario).

GET /api/v1/calendario/resumen?anio=2026
- 1 request reemplaza ~40 paginados legacy.
- Respuesta: espacios + celdas GROUP BY + eventos detalle + por_mes.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.calendario import ResumenCalendarioResponse
from app.services import calendario as calendario_service
from app.core.security import require_role

router = APIRouter(
    prefix="/calendario",
    tags=["calendario"],
    responses={500: {"description": "Error interno"}},
)


@router.get(
    "/resumen",
    response_model=ResumenCalendarioResponse,
    summary="Resumen anual agregado para la matriz 12x31",
    description="""
    Devuelve en **un solo request** lo que el calendario legacy hacía en ~40:

    - `espacios`: filas canónicas con `total` anual.
    - `celdas`: solo días con eventos, pre-agrupados por (espacio, mes, día).
    - `eventos`: detalle para modal solo-lectura y lista móvil.
    - `por_mes`: conteo ene..dic para KPIs.

    **Ejemplo:** `GET /api/v1/calendario/resumen?anio=2026`
    """,
    dependencies=[
        Depends(
            require_role(
                "Jefe de Infraestructura",
                "Auxiliar de Infraestructura",
                "Tecnico",
            )
        )
    ],
)
def obtener_resumen_anual(
    anio: int = Query(..., ge=2000, le=2100, description="Año YYYY"),
    db: Session = Depends(get_db),
) -> ResumenCalendarioResponse:
    try:
        datos = calendario_service.obtener_resumen_anual(db, anio=anio)
        return ResumenCalendarioResponse(**datos)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al agregar resumen anual: {str(e)}",
        )
