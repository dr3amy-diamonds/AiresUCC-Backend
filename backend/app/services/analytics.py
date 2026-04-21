"""
Módulo de análisis y procesamiento de datos de mantenimiento.
Utiliza Pandas para generar KPIs y métricas sobre la gestión de aires acondicionados.
"""

from typing import List, Dict, Any
from dataclasses import dataclass
import pandas as pd


@dataclass
class ResumenAnalytica:
    """Estructura de datos para los resultados del análisis de mantenimiento."""
    conteo_fallas_por_equipo: Dict[str, int]
    porcentaje_cumplimiento_preventivo: float
    equipos_operativos: int
    equipos_fuera_servicio: int
    total_equipos: int


class MaintenanceAnalytics:
    """
    Clase para análisis y procesamiento de datos de mantenimiento.
    Utiliza Pandas para calcular métricas, KPIs y resúmenes de estado de equipos.
    """

    def __init__(self):
        """Inicializa la clase con valores por defecto."""
        pass

    def calcular_metricas(self, mantenimientos: List[Dict[str, Any]]) -> ResumenAnalytica:
        """
        Calcula métricas clave de mantenimiento a partir de una lista de registros.

        Args:
            mantenimientos (List[Dict]): Lista de diccionarios con registros de mantenimiento.
                Esperado que contenga campos como:
                - 'equipo_id': ID del equipo
                - 'equipo_serial': Serial del equipo
                - 'tipo_mantenimiento': Tipo ('Preventivo' o 'Correctivo')
                - 'estado_equipo': Estado actual ('Operativo', 'En reparacion', 'Inactivo', 'Dado de baja')

        Returns:
            ResumenAnalytica: Objeto con las métricas calculadas.

        Ejemplo:
            >>> mantenimientos = [
            ...     {'equipo_id': 1, 'equipo_serial': 'LG001', 'tipo_mantenimiento': 'Preventivo', 'estado_equipo': 'Operativo'},
            ...     {'equipo_id': 2, 'equipo_serial': 'SAMSUNG02', 'tipo_mantenimiento': 'Correctivo', 'estado_equipo': 'En reparacion'}
            ... ]
            >>> analytics = MaintenanceAnalytics()
            >>> resumen = analytics.calcular_metricas(mantenimientos)
        """
        # Convertir lista a DataFrame de Pandas para análisis
        if not mantenimientos:
            return ResumenAnalytica(
                conteo_fallas_por_equipo={},
                porcentaje_cumplimiento_preventivo=0.0,
                equipos_operativos=0,
                equipos_fuera_servicio=0,
                total_equipos=0
            )

        df = pd.DataFrame(mantenimientos)

        # 1. Conteo de fallas por equipo
        conteo_fallas = self._calcular_conteo_fallas(df)

        # 2. Porcentaje de cumplimiento de mantenimientos preventivos
        porcentaje_preventivo = self._calcular_cumplimiento_preventivo(df)

        # 3. Resumen de equipos operativos vs. fuera de servicio
        equipos_operativos, equipos_fuera_servicio, total_equipos = self._calcular_estado_equipos(df)

        return ResumenAnalytica(
            conteo_fallas_por_equipo=conteo_fallas,
            porcentaje_cumplimiento_preventivo=porcentaje_preventivo,
            equipos_operativos=equipos_operativos,
            equipos_fuera_servicio=equipos_fuera_servicio,
            total_equipos=total_equipos
        )

    def _calcular_conteo_fallas(self, df: pd.DataFrame) -> Dict[str, int]:
        """
        Calcula el conteo de fallas (mantenimientos correctivos) por equipo.

        Args:
            df (pd.DataFrame): DataFrame con registros de mantenimiento.

        Returns:
            Dict[str, int]: Diccionario con serial del equipo como clave y conteo de fallas como valor.
        """
        # Filtrar solo mantenimientos correctivos (fallas)
        fallas_df = df[df['tipo_mantenimiento'] == 'Correctivo']

        # Agrupar por serial del equipo y contar
        if len(fallas_df) == 0:
            return {}

        conteo = fallas_df.groupby('equipo_serial').size().to_dict()
        return conteo

    def _calcular_cumplimiento_preventivo(self, df: pd.DataFrame) -> float:
        """
        Calcula el porcentaje de mantenimientos preventivos vs. total de mantenimientos.

        Args:
            df (pd.DataFrame): DataFrame con registros de mantenimiento.

        Returns:
            float: Porcentaje de cumplimiento de mantenimientos preventivos (0-100).
        """
        total_registros = len(df)

        if total_registros == 0:
            return 0.0

        preventivos = len(df[df['tipo_mantenimiento'] == 'Preventivo'])
        porcentaje = (preventivos / total_registros) * 100

        return round(porcentaje, 2)

    def _calcular_estado_equipos(self, df: pd.DataFrame) -> tuple:
        """
        Calcula el resumen de equipos operativos vs. fuera de servicio.

        Args:
            df (pd.DataFrame): DataFrame con registros de equipos.

        Returns:
            tuple: (equipos_operativos, equipos_fuera_servicio, total_equipos).
        """
        # Obtener únicos equipos para evitar duplicados si hay múltiples mantenimientos
        equipos_unicos = df.drop_duplicates(subset=['equipo_id'])

        total_equipos = len(equipos_unicos)

        # Contar estados
        operativos = len(equipos_unicos[equipos_unicos['estado_equipo'] == 'Operativo'])
        fuera_servicio = total_equipos - operativos

        return operativos, fuera_servicio, total_equipos

    def generar_reporte_csv(
        self,
        mantenimientos: List[Dict[str, Any]],
        ruta_salida: str
    ) -> bool:
        """
        Genera un reporte en formato CSV con los datos de mantenimiento.

        Args:
            mantenimientos (List[Dict]): Lista de registros de mantenimiento.
            ruta_salida (str): Ruta donde guardar el archivo CSV.

        Returns:
            bool: True si se generó correctamente, False en caso contrario.

        Ejemplo:
            >>> analytics = MaintenanceAnalytics()
            >>> exito = analytics.generar_reporte_csv(mantenimientos, "reporte_mantenimiento.csv")
        """
        try:
            if not mantenimientos:
                return False

            df = pd.DataFrame(mantenimientos)
            df.to_csv(ruta_salida, index=False, encoding='utf-8')
            return True
        except Exception:
            return False


