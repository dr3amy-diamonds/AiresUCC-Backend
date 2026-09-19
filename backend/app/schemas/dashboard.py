"""DTOs de agregación para el dashboard (/dashboard/resumen)."""

from pydantic import BaseModel, Field


class FlotaResumenDTO(BaseModel):
    """Bloque flota: regla tipo_equipo_id IN (1, 2, 5) = Chiller."""

    total_equipos: int = Field(..., description="Conteo general de la flota")
    total_chiller: int = Field(..., description="Centrales (1, 2) + Piso Techo (5)")
    total_otros: int = Field(..., description="Mini Splits y demás sistemas autónomos")


class FinancieroResumenDTO(BaseModel):
    """Bloque financiero: presupuesto vs insumos consumidos."""

    presupuesto_asignado: int = Field(..., description="Monto límite asignado por administración")
    total_gastado: int = Field(..., description="Suma de insumos utilizados en mantenimientos")
    saldo_disponible: int = Field(..., description="Presupuesto menos total gastado")


class DashboardResumenUnificadoDTO(BaseModel):
    """Payload unificado GET /api/v1/dashboard/resumen."""

    flota: FlotaResumenDTO
    financiero: FinancieroResumenDTO
    # Campos planos duplicados para compatibilidad con loaders antiguos.
    total_equipos: int = Field(..., description="Duplicado plano de flota.total_equipos")
    total_chiller: int = Field(..., description="Duplicado plano de flota.total_chiller")
    total_otros: int = Field(..., description="Duplicado plano de flota.total_otros")
