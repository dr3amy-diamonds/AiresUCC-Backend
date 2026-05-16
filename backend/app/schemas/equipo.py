"""
Esquemas Pydantic para la entidad Equipo.
Define los contratos de validación para la entrada y salida de datos de los aires acondicionados.
"""

from datetime import date
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal


class EquipoBase(BaseModel):
    """
    Base schema para Equipo. Define los atributos técnicos comunes.

    Atributos:
        codigo_activo (str): Plaqueta de inventario oficial de la UCC.
        modelo (str): Referencia técnica o modelo del fabricante (ej: HCH45P17C).
        capacidad_btu (int): Potencia térmica del equipo en BTU.
        tonelaje (Decimal): Capacidad de refrigeración en toneladas (ej: 3.58).
        numero_serie (str): Serial único de fábrica para garantías y soporte.
        fecha_instalacion (date): Fecha en que se montó el equipo en el campus.
        ultima_fecha (date): Fecha del último mantenimiento preventivo o correctivo realizado.
        proxima_fecha (date): Fecha programada para la siguiente intervención técnica.
        estado (str): Situación operativa (Operativo, En reparación, Inactivo, Dado de baja).
        marca_id (int): Identificador de la marca fabricante.
        tipo_equipo_id (int): Identificador de la categoría del equipo.
        espacio_id (int): Identificador del aula o oficina donde está ubicado.
    """
    codigo_activo: str = Field(..., min_length=1, max_length=50, description="Plaqueta de inventario oficial de la UCC")
    modelo: Optional[str] = Field(None, max_length=50, description="Modelo o referencia técnica del equipo")
    capacidad_btu: int = Field(..., gt=0, description="Capacidad en BTU del equipo")

    # --- NUEVOS CAMPOS MVP ---
    tonelaje: Optional[Decimal] = Field(None, max_digits=4, decimal_places=2, description="Capacidad en toneladas")
    numero_serie: Optional[str] = Field(None, max_length=60, description="Serial de fábrica")
    ultima_fecha: Optional[date] = Field(None, description="Fecha del último mantenimiento")
    proxima_fecha: Optional[date] = Field(None, description="Fecha del próximo mantenimiento")
    # -------------------------

    fecha_instalacion: Optional[date] = Field(None, description="Fecha de instalación del equipo")
    estado: str = Field(default="Operativo", description="Estado operativo actual")
    marca_id: int = Field(..., description="ID de la marca")
    tipo_equipo_id: int = Field(..., description="ID del tipo de equipo")
    espacio_id: int = Field(..., description="ID del espacio físico")


class EquipoCreate(EquipoBase):
    """Schema para la creación de un nuevo registro de equipo."""
    pass


class EquipoUpdate(BaseModel):
    """
    Schema para la actualización parcial de un equipo.
    Permite modificar solo los campos necesarios sin afectar el resto.
    """
    modelo: Optional[str] = None
    capacidad_btu: Optional[int] = None
    tonelaje: Optional[Decimal] = None
    numero_serie: Optional[str] = None
    ultima_fecha: Optional[date] = None
    proxima_fecha: Optional[date] = None
    estado: Optional[str] = None
    espacio_id: Optional[int] = None


class EquipoResponse(EquipoBase):
    """
    Schema de respuesta que incluye el ID generado por la base de datos.
    Se utiliza para enviar datos desde el FastAPI hacia el Frontend.
    """
    id: int = Field(..., description="ID único incremental del equipo")

    model_config = ConfigDict(from_attributes=True)


class EquipoListResponse(BaseModel):
    """
    Schema de respuesta para listas paginadas de equipos.
    Incluye metadata de paginación e items.
    """
    total: int = Field(..., description="Total de registros en la base de datos")
    page: int = Field(..., description="Número de página actual")
    size: int = Field(..., description="Cantidad de items por página")
    items: list[EquipoResponse] = Field(..., description="Lista de equipos")
