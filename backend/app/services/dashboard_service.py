"""
Servicio de Analítica y Dashboard.

Este módulo consulta la base de datos y transforma resultados en KPIs
para alimentar dashboards, reportes ejecutivos y gráficos.

Utiliza:
- Pandas para procesamiento eficiente
- SQLAlchemy ORM para queries
- MaintenanceAnalytics para cálculos complejos

KPIs Principales:
1. Disponibilidad General: % de equipos operativos
2. Cumplimiento Preventivo: % de mantenimientos preventivos vs correctivos
3. Fallas por Equipo: Ranking de aires problemáticos
4. Carga de Trabajo: Mantenimientos por tecnician
5. Tendencias: Evolución de disponibilidad en el tiempo
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
import pandas as pd

from app.models.mantenimiento import Mantenimiento
from app.models.programacion import Programacion
from app.models.equipo import Equipo
from app.models.usuario import Usuario
from app.models.tipo_mantenimiento import TipoMantenimiento
from app.services.analytics import MaintenanceAnalytics


# ============================================================================
# FUNCIONES DE CONSULTA Y EXTRACCIÓN DE DATOS
# ============================================================================

def obtener_datos_mantenimientos_para_analytics(
    db: Session,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
) -> List[Dict[str, Any]]:
    """
    Extrae datos de mantenimientos en formato JSON para Pandas.
    
    Args:
        db (Session): Sesión de SQLAlchemy
        fecha_desde (Optional[date]): Filtro fecha inicio (default: 90 días atrás)
        fecha_hasta (Optional[date]): Filtro fecha fin (default: hoy)
        
    Returns:
        List[Dict]: Lista de diccionarios para convertir a DataFrame
    """
    if fecha_desde is None:
        fecha_desde = datetime.now().date() - timedelta(days=90)
    if fecha_hasta is None:
        fecha_hasta = datetime.now().date()
    
    # Query con JOINs para obtener datos completos
    mantenimientos = (
        db.query(
            Mantenimiento.id,
            Mantenimiento.fecha_mantenimiento,
            Equipo.id.label("equipo_id"),
            Equipo.codigo_activo,
            Equipo.modelo,
            Equipo.estado.label("estado_equipo"),
            TipoMantenimiento.nombre.label("tipo_mantenimiento"),
            Usuario.nombre.label("tecnico_nombre"),
            Usuario.id.label("tecnico_id"),
        )
        .join(Equipo, Mantenimiento.equipo_id == Equipo.id)
        .join(TipoMantenimiento, Mantenimiento.tipo_mantenimiento_id == TipoMantenimiento.id)
        .join(Usuario, Mantenimiento.encargado_id == Usuario.id)
        .filter(Mantenimiento.fecha_mantenimiento.between(fecha_desde, fecha_hasta))
        .all()
    )
    
    # Convertir a diccionarios para DataFrame
    return [
        {
            "id": m.id,
            "fecha_mantenimiento": m.fecha_mantenimiento,
            "equipo_id": m.equipo_id,
            "equipo_serial": m.codigo_activo,
            "equipo_modelo": m.modelo,
            "estado_equipo": m.estado_equipo,
            "tipo_mantenimiento": m.tipo_mantenimiento,
            "tecnico_nombre": m.tecnico_nombre,
            "tecnico_id": m.tecnico_id,
        }
        for m in mantenimientos
    ]


def obtener_estado_equipos(db: Session) -> List[Dict[str, Any]]:
    """
    Extrae estado actual de todos los equipos para disponibilidad.
    
    Returns:
        List[Dict]: Equipos con su estado actual
    """
    equipos = (
        db.query(
            Equipo.id,
            Equipo.codigo_activo,
            Equipo.modelo,
            Equipo.estado,
            Equipo.capacidad_btu,
        )
        .all()
    )
    
    return [
        {
            "equipo_id": e.id,
            "codigo_activo": e.codigo_activo,
            "modelo": e.modelo,
            "estado": e.estado,
            "btu": e.capacidad_btu,
        }
        for e in equipos
    ]


def obtener_programaciones_estado(db: Session) -> Dict[str, int]:
    """
    Cuenta programaciones por estado actual.
    
    Returns:
        Dict: {'Pendiente': count, 'Completado': count, ...}
    """
    resultados = (
        db.query(Programacion.estado, func.count(Programacion.id))
        .group_by(Programacion.estado)
        .all()
    )
    
    return {estado: count for estado, count in resultados}


# ============================================================================
# CÁLCULO DE KPIs PRINCIPALES
# ============================================================================

def calcular_disponibilidad_general(db: Session) -> Dict[str, Any]:
    """
    Calcula disponibilidad global del parque térmico.
    
    Returns:
        Dict: {
            'total_equipos': int,
            'equipos_operativos': int,
            'equipos_fuera_servicio': int,
            'porcentaje_disponibilidad': float,
            'capacidad_btu_total': int,
            'capacidad_operativa': int,
        }
    """
    # Contar equipos y agrupación por estado
    total_equipos = db.query(func.count(Equipo.id)).scalar() or 0
    
    operativos = (
        db.query(func.count(Equipo.id))
        .filter(Equipo.estado == "Operativo")
        .scalar() or 0
    )
    
    fuera_servicio = total_equipos - operativos
    
    # Capacidad BTU
    capacidad_total = (
        db.query(func.sum(Equipo.capacidad_btu))
        .scalar() or 0
    )
    
    capacidad_operativa = (
        db.query(func.sum(Equipo.capacidad_btu))
        .filter(Equipo.estado == "Operativo")
        .scalar() or 0
    )
    
    # Porcentaje
    porcentaje = round(
        (operativos / total_equipos * 100) if total_equipos > 0 else 0,
        2
    )
    
    return {
        "total_equipos": total_equipos,
        "equipos_operativos": operativos,
        "equipos_fuera_servicio": fuera_servicio,
        "porcentaje_disponibilidad": porcentaje,
        "capacidad_btu_total": int(capacidad_total),
        "capacidad_operativa": int(capacidad_operativa),
    }


def calcular_cumplimiento_preventivo(
    db: Session,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
) -> Dict[str, Any]:
    """
    Calcula proporción de mantenimientos preventivos vs correctivos.
    
    KPI CRÍTICO: Mide efectividad de estrategia preventiva.
    
    Returns:
        Dict: {
            'total_mantenimientos': int,
            'preventivos': int,
            'correctivos': int,
            'porcentaje_preventivo': float,
            'ratio_correctivo_preventivo': float,
        }
    """
    if fecha_desde is None:
        fecha_desde = datetime.now().date() - timedelta(days=30)
    if fecha_hasta is None:
        fecha_hasta = datetime.now().date()
    
    # Contar mantenimientos totales en período
    total = (
        db.query(func.count(Mantenimiento.id))
        .filter(Mantenimiento.fecha_mantenimiento.between(fecha_desde, fecha_hasta))
        .scalar() or 0
    )
    
    # Contar preventivos (Preventivo = preventivo, Correctivo = correctivo)
    preventivos = (
        db.query(func.count(Mantenimiento.id))
        .join(TipoMantenimiento, Mantenimiento.tipo_mantenimiento_id == TipoMantenimiento.id)
        .filter(
            TipoMantenimiento.nombre == "Preventivo",
            Mantenimiento.fecha_mantenimiento.between(fecha_desde, fecha_hasta)
        )
        .scalar() or 0
    )
    
    correctivos = total - preventivos
    
    # Cálculos
    porcentaje_preventivo = round(
        (preventivos / total * 100) if total > 0 else 0,
        2
    )
    
    ratio_correctivo = round(
        (correctivos / preventivos) if preventivos > 0 else 0,
        2
    )
    
    return {
        "total_mantenimientos": total,
        "preventivos": preventivos,
        "correctivos": correctivos,
        "porcentaje_preventivo": porcentaje_preventivo,
        "ratio_correctivo_preventivo": ratio_correctivo,
        "periodo_analizado": f"{fecha_desde} a {fecha_hasta}",
    }


def obtener_equipos_problematicos(
    db: Session,
    limit: int = 10,
    fecha_desde: Optional[date] = None,
) -> List[Dict[str, Any]]:
    """
    Identifica equipos con más mantenimientos correctivos (problemas recurrentes).
    
    Útil para alertas de costo/reemplazo.
    
    Args:
        db (Session): Sesión de SQLAlchemy
        limit (int): Top N equipos
        fecha_desde (Optional[date]): Período de análisis (default: últimos 90 días)
        
    Returns:
        List[Dict]: Ranking de equipos por problema
    """
    if fecha_desde is None:
        fecha_desde = datetime.now().date() - timedelta(days=90)
    
    # Query complexa: contar CORRECTIVOS por equipo
    resultados = (
        db.query(
            Equipo.id,
            Equipo.codigo_activo,
            Equipo.modelo,
            Equipo.estado,
            func.count(Mantenimiento.id).label("correctivos_count")
        )
        .join(Mantenimiento, Equipo.id == Mantenimiento.equipo_id)
        .join(TipoMantenimiento, Mantenimiento.tipo_mantenimiento_id == TipoMantenimiento.id)
        .filter(
            TipoMantenimiento.nombre == "Correctivo",
            Mantenimiento.fecha_mantenimiento >= fecha_desde
        )
        .group_by(Equipo.id, Equipo.codigo_activo, Equipo.modelo, Equipo.estado)
        .order_by(func.count(Mantenimiento.id).desc())
        .limit(limit)
        .all()
    )
    
    return [
        {
            "equipo_id": r.id,
            "codigo_activo": r.codigo_activo,
            "modelo": r.modelo,
            "estado": r.estado,
            "correctivos_count": r.correctivos_count,
            "recomendacion": "CRÍTICO: Evaluar reemplazo" if r.correctivos_count >= 5 else "Alertar"
        }
        for r in resultados
    ]


def obtener_carga_tecnicos(
    db: Session,
    fecha_desde: Optional[date] = None,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """
    Analiza carga de trabajo de técnicos (mantenimientos realizados).
    
    Útil para balanceo de recursos.
    
    Args:
        db (Session): Sesión de SQLAlchemy
        fecha_desde (Optional[date]): Período de análisis (default: últimos 30 días)
        limit (int): Top N técnicos a retornar (default: 10)
    
    Returns:
        List[Dict]: Técnicos con sus estadísticas de carga
    """
    if fecha_desde is None:
        fecha_desde = datetime.now().date() - timedelta(days=30)
    
    resultados = (
        db.query(
            Usuario.id,
            Usuario.nombre,
            func.count(Mantenimiento.id).label("mantenimientos_realizados")
        )
        .join(Mantenimiento, Usuario.id == Mantenimiento.encargado_id)
        .filter(Mantenimiento.fecha_mantenimiento >= fecha_desde)
        .group_by(Usuario.id, Usuario.nombre)
        .order_by(func.count(Mantenimiento.id).desc())
        .limit(limit)
        .all()
    )
    
    return [
        {
            "tecnico_id": r.id,
            "tecnico_nombre": r.nombre,
            "mantenimientos": r.mantenimientos_realizados,
            "promedio_por_dia": round(r.mantenimientos_realizados / 30, 2)
        }
        for r in resultados
    ]


# ============================================================================
# COMPOSITE: DASHBOARD COMPLETO
# ============================================================================

def calcular_kpis_financieros_y_mantenimiento(db: Session) -> Dict[str, Any]:
    """
    Calcula KPIs específicos para análisis financiero y alertas de mantenimiento.

    KPIs Incluidos:
    - Gasto Total: Sumatoria de costo_mano_obra en mantenimientos
    - Capacidad Instalada Total: Sumatoria de tonelaje en equipos
    - Alertas de Mantenimiento: Equipos con proxima_fecha vencida, a punto de vencer, o sin fecha

    Returns:
        Dict: {
            'gasto_total': float,
            'capacidad_instalada_total': float,
            'equipos_alerta_mantenimiento': int,
            'equipos_mantenimiento_vencido': int,
            'equipos_a_punto_vencer': int,
            'equipos_sin_fecha_proxima': int,
        }
    """
    # 1. GASTO TOTAL: Suma de costo_mano_obra
    gasto_total = (
        db.query(func.sum(Mantenimiento.costo_mano_obra))
        .scalar() or 0
    )
    gasto_total = float(gasto_total) if gasto_total else 0.0

    # 2. CAPACIDAD INSTALADA TOTAL: Suma de tonelaje
    capacidad_total = (
        db.query(func.sum(Equipo.tonelaje))
        .scalar() or 0
    )
    capacidad_total = float(capacidad_total) if capacidad_total else 0.0

    # 3. ALERTAS DE MANTENIMIENTO: Equipos con proxima_fecha vencida, a punto de vencer, o nula
    fecha_actual = datetime.now().date()
    fecha_alerta = fecha_actual + timedelta(days=15)

    # Equipos con proxima_fecha menor a hoy (vencidos)
    equipos_vencidos = (
        db.query(func.count(Equipo.id))
        .filter(
            Equipo.proxima_fecha < fecha_actual,
            Equipo.proxima_fecha.isnot(None)
        )
        .scalar() or 0
    )

    # Equipos a punto de vencer (proxima_fecha entre hoy y hoy+15 días)
    equipos_a_punto_vencer = (
        db.query(func.count(Equipo.id))
        .filter(
            Equipo.proxima_fecha >= fecha_actual,
            Equipo.proxima_fecha <= fecha_alerta,
            Equipo.proxima_fecha.isnot(None)
        )
        .scalar() or 0
    )

    # Equipos sin fecha próxima definida (acción requerida)
    equipos_sin_fecha = (
        db.query(func.count(Equipo.id))
        .filter(Equipo.proxima_fecha.is_(None))
        .scalar() or 0
    )

    # Total de equipos en alerta
    equipos_alerta = equipos_vencidos + equipos_a_punto_vencer + equipos_sin_fecha

    return {
        "gasto_total": gasto_total,
        "capacidad_instalada_total": capacidad_total,
        "equipos_alerta_mantenimiento": equipos_alerta,
        "equipos_mantenimiento_vencido": equipos_vencidos,
        "equipos_a_punto_vencer": equipos_a_punto_vencer,
        "equipos_sin_fecha_proxima": equipos_sin_fecha,
    }


def generar_dashboard_completo(db: Session) -> Dict[str, Any]:
    """
    Genera un dashboard ejecutivo completo con todos los KPIs.
    
    Este es el ENDPOINT PRINCIPAL para /api/v1/stats.
    Incluye: disponibilidad, cumplimiento preventivo, KPIs financieros y alertas de mantenimiento.

    Returns:
        Dict: Estructura JSON lista para serializar a cliente
    """
    # Metadatos
    timestamp_generacion = datetime.now().isoformat()
    
    # KPIs principales
    disponibilidad = calcular_disponibilidad_general(db)
    cumplimiento = calcular_cumplimiento_preventivo(db)
    programaciones = obtener_programaciones_estado(db)
    
    # KPIs financieros y de mantenimiento (NUEVOS)
    kpis_financieros = calcular_kpis_financieros_y_mantenimiento(db)

    # Datos detallados
    equipos_problematicos = obtener_equipos_problematicos(db, limit=5)
    carga_tecnicos = obtener_carga_tecnicos(db, limit=5)
    
    # Análisis con Pandas
    datos_mant = obtener_datos_mantenimientos_para_analytics(db)
    analytics = MaintenanceAnalytics()
    resumen_analytics = analytics.calcular_metricas(datos_mant)
    
    # Composición final
    dashboard = {
        "timestamp": timestamp_generacion,
        "resumen_disponibilidad": disponibilidad,
        "cumplimiento_preventivo": cumplimiento,
        "programaciones_estado": programaciones,
        "kpis_financieros": {
            "gasto_total_mano_obra": kpis_financieros["gasto_total"],
            "capacidad_instalada_total_toneladas": kpis_financieros["capacidad_instalada_total"],
        },
        "alertas": {
            "equipos_problematicos": equipos_problematicos,
            "carga_tecnicos": carga_tecnicos,
            "mantenimiento": {
                "equipos_en_alerta": kpis_financieros["equipos_alerta_mantenimiento"],
                "equipos_vencidos": kpis_financieros["equipos_mantenimiento_vencido"],
                "equipos_a_punto_vencer": kpis_financieros["equipos_a_punto_vencer"],
                "equipos_sin_fecha": kpis_financieros["equipos_sin_fecha_proxima"],
            },
        },
        "metricas_pandas": {
            "conteo_fallas_por_equipo": resumen_analytics.conteo_fallas_por_equipo,
            "porcentaje_cumplimiento": resumen_analytics.porcentaje_cumplimiento_preventivo,
            "equipos_operativos": resumen_analytics.equipos_operativos,
            "equipos_fuera_servicio": resumen_analytics.equipos_fuera_servicio,
            "total_equipos": resumen_analytics.total_equipos,
        }
    }
    
    return dashboard


def generar_reporte_exportable(
    db: Session,
    formato: str = "json"
) -> Dict[str, Any]:
    """
    Genera reporte exportable (JSON, CSV en futuros desarrollos).
    
    Args:
        db (Session): Sesión de SQLAlchemy
        formato (str): 'json' (extendible a 'csv', 'xlsx')
        
    Returns:
        Dict: Datos estructurados para exportar
    """
    dashboard = generar_dashboard_completo(db)
    
    if formato == "json":
        return dashboard
    else:
        # Extensible para CSV, Excel, etc
        raise NotImplementedError(f"Formato {formato} no implementado aún")


"""
INTEGRACIÓN EN ENDPOINTS:

@router.get("/stats", response_model=DashboardResponse)
def obtener_estadisticas(db: Session = Depends(get_db)):
    dashboard = dashboard_service.generar_dashboard_completo(db)
    return dashboard

Respuesta esperada (JSON):
{
    "timestamp": "2026-05-05T14:30:00",
    "resumen_disponibilidad": {
        "total_equipos": 150,
        "equipos_operativos": 142,
        "porcentaje_disponibilidad": 94.67,
        ...
    },
    "cumplimiento_preventivo": {
        "total_mantenimientos": 23,
        "preventivos": 18,
        "porcentaje_preventivo": 78.26,
        ...
    },
    ...
}
"""

