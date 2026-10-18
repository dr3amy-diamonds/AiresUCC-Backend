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


class EstadoEquiposDTO(BaseModel):
    """Bloque estado: conteo real por estado operativo."""

    operativos: int = Field(..., description="Equipos en estado Operativo")
    en_reparacion: int = Field(..., description="Equipos en estado En reparacion")
    inactivos: int = Field(..., description="Equipos en estado Inactivo")
    dados_baja: int = Field(..., description="Equipos en estado Dado de baja")


class MantenimientosMesDTO(BaseModel):
    """Bloque mensual: actividad del mes en curso."""

    realizados: int = Field(..., description="Mantenimientos ejecutados en el mes")
    programados: int = Field(..., description="Programaciones creadas en el mes")
    pendientes: int = Field(..., description="Programaciones pendientes del mes")
    vencidos: int = Field(..., description="Programaciones vencidas del mes")


class DashboardResumenUnificadoDTO(BaseModel):
    """Payload unificado GET /api/v1/dashboard/resumen."""

    flota: FlotaResumenDTO
    financiero: FinancieroResumenDTO
    estado_equipos: EstadoEquiposDTO
    mantenimientos_mes: MantenimientosMesDTO
    # Campos planos duplicados para compatibilidad con loaders antiguos.
    total_equipos: int = Field(..., description="Duplicado plano de flota.total_equipos")
    total_chiller: int = Field(..., description="Duplicado plano de flota.total_chiller")
    total_otros: int = Field(..., description="Duplicado plano de flota.total_otros")
