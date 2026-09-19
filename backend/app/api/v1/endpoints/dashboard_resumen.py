"""Resumen de equipos y resumen financiero (/dashboard/resumen)."""

import os
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.equipo import Equipo
from app.models.componente_usado import ComponenteUsado
from app.schemas.dashboard import DashboardResumenUnificadoDTO

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
    responses={500: {"description": "Error interno del servidor"}},
)

# Regla de negocio: centrales (1, 2) + Piso Techo (5) = Chiller.
CHILLER_TIPOS = (1, 2, 5)
PRESUPUESTO_DEFAULT = 80000000


def _presupuesto_asignado() -> int:
    try:
        return int(os.getenv("PRESUPUESTO_ASIGNADO", str(PRESUPUESTO_DEFAULT)))
    except ValueError:
        return PRESUPUESTO_DEFAULT


@router.get(
    "/resumen",
    response_model=DashboardResumenUnificadoDTO,
    summary="Resumen de equipos y resumen financiero",
)
def obtener_resumen(db: Session = Depends(get_db)) -> DashboardResumenUnificadoDTO:
    """Cuenta flota por tipo_equipo_id y calcula presupuesto vs insumos."""
    try:
        resumen = db.query(
            func.count(Equipo.id).label("total_equipos"),
            func.count(case((Equipo.tipo_equipo_id.in_(CHILLER_TIPOS), 1))).label("total_chiller"),
        ).filter(Equipo.estado != "Inactivo").first()
        total_equipos = int(resumen.total_equipos or 0)
        total_chiller = int(resumen.total_chiller or 0)
        total_otros = max(total_equipos - total_chiller, 0)

        gasto = db.query(
            func.coalesce(func.sum(ComponenteUsado.cantidad * ComponenteUsado.precio_unitario), 0)
        ).scalar() or 0
        total_gastado = int(float(gasto))
        presupuesto = _presupuesto_asignado()
        saldo = presupuesto - total_gastado

        flota = {
            "total_equipos": total_equipos,
            "total_chiller": total_chiller,
            "total_otros": total_otros,
        }
        financiero = {
            "presupuesto_asignado": presupuesto,
            "total_gastado": total_gastado,
            "saldo_disponible": saldo,
        }
        return DashboardResumenUnificadoDTO(
            flota=flota,
            financiero=financiero,
            total_equipos=total_equipos,
            total_chiller=total_chiller,
            total_otros=total_otros,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )
