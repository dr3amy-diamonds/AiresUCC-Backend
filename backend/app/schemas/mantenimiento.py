"""
Esquemas Pydantic para la entidad Mantenimiento.

Este módulo define los contratos de validación de datos para:
- Creación de registros de mantenimiento
- Actualización de datos de mantenimiento
- Respuestas planas y seguras (SIN relaciones anidadas complejas)
- Enumeraciones de estados de mantenimiento

Arquitectura:
- Validación estricta con Pydantic v2
- Base de datos PLANA: solo IDs y valores directos en respuestas
- Timestamps automáticos de BD (no cliente)
- Sincronización exacta con modelo SQLAlchemy
- Documentación completa con ejemplos
"""

from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from enum import Enum


INSUMOS_FIJOS_TALLER = frozenset({
    "Capacitor de Marcha",
    "Bomba de Condensación",
    "Embobinado de Motor",
})


# ============================================================================
# ENUMS Y CONSTANTES
# ============================================================================

class EstadoMantenimientoEnum(str, Enum):
    """Estados posibles de un mantenimiento registrado."""
    PENDIENTE = "Pendiente"
    EN_PROGRESO = "En progreso"
    COMPLETADO = "Completado"
    CANCELADO = "Cancelado"
    VENCIDO = "Vencido"


class TipoMantenimientoEnum(str, Enum):
    """Tipos de mantenimiento soportados."""
    PREVENTIVO = "Preventivo"
    CORRECTIVO = "Correctivo"
    INSPECCION = "Inspección"


# ============================================================================
# ESQUEMAS BASE Y CREATE
# ============================================================================

class MantenimientoBase(BaseModel):
    """
    Esquema base con campos comunes de mantenimiento.

    Contiene los atributos esenciales compartidos entre creación y respuesta.
    """
    equipo_id: int = Field(
        ...,
        gt=0,
        description="ID del equipo a mantener (debe existir en BD)"
    )
    encargado_id: int = Field(
        ...,
        gt=0,
        description="ID del técnico responsable de realizar el mantenimiento"
    )
    tipo_mantenimiento_id: int = Field(
        ...,
        gt=0,
        description="ID del tipo de mantenimiento (Preventivo, Correctivo, etc)"
    )
    detalle_mantenimiento: Optional[str] = Field(
        None,
        max_length=1000,
        description="Descripción detallada del trabajo realizado"
    )
    costo_servicio: float = Field(
        default=0.0,
        ge=0,
        description="Costo del servicio técnico en pesos"
    )


class MantenimientoCreate(MantenimientoBase):
    """
    Esquema para creación de nuevo registro de mantenimiento.

    Validación Pydantic:
    - Todos los IDs foráneos deben ser positivos
    - El detalle es opcional pero recomendado
    - La fecha de mantenimiento es hoy por defecto
    - El técnico que registra es el usuario autenticado (del JWT)

    Nota: La contraseña y datos sensibles se validan en el servicio.
    """
    fecha_mantenimiento: date = Field(
        default_factory=lambda: datetime.now().date(),
        description="Fecha de realización del mantenimiento (YYYY-MM-DD)"
    )
    registrado_por: int = Field(
        ...,
        gt=0,
        description="ID del usuario que registra el mantenimiento en el sistema"
    )


class ComponenteUsadoInput(BaseModel):
    """Insumo consumido en el cierre de orden: fijo (por ID) o adicional (por nombre)."""
    repuesto_utilizado_id: Optional[int] = Field(
        None, gt=0, description="ID del insumo fijo del catálogo",
    )
    nombre: Optional[str] = Field(
        None, min_length=2, max_length=60, description="Nombre libre para insumos adicionales",
    )
    cantidad: float = Field(..., gt=0, description="Cantidad utilizada")
    precio_unitario: float = Field(..., ge=0, description="Valor unitario en COP")

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validar_referencia_insumo(self) -> "ComponenteUsadoInput":
        tiene_id = self.repuesto_utilizado_id is not None
        tiene_nombre = bool((self.nombre or "").strip())
        if tiene_id == tiene_nombre:
            raise ValueError(
                "Cada insumo debe indicar repuesto_utilizado_id (fijo) o nombre (adicional), no ambos."
            )
        return self


class CerrarOrdenRequest(BaseModel):
    """
    Payload para el cierre técnico atómico de una orden de programación.

    El costo_servicio proviene exclusivamente de la sumatoria de materiales
    consumidos en taller (sin mano de obra).
    """
    fecha_mantenimiento: date = Field(
        ...,
        description="Fecha en que se ejecutó el servicio de campo (YYYY-MM-DD)",
    )
    detalle_mantenimiento: str = Field(
        ...,
        min_length=15,
        max_length=4000,
        description="Descripción técnica del trabajo realizado (mínimo 15 caracteres)",
    )
    costo_servicio: float = Field(
        ...,
        ge=0,
        description="Costo total del servicio = sumatoria lineal de materiales consumidos",
    )
    componentes: List[ComponenteUsadoInput] = Field(
        default_factory=list,
        description="Insumos fijos y adicionales consumidos en el servicio",
    )

    @field_validator("detalle_mantenimiento")
    @classmethod
    def validar_detalle_no_vacio(cls, valor: str) -> str:
        limpio = valor.strip()
        if len(limpio) < 15:
            raise ValueError("El detalle del mantenimiento debe tener al menos 15 caracteres")
        return limpio

    @model_validator(mode="after")
    def validar_costo_coherente_con_componentes(self) -> "CerrarOrdenRequest":
        total_componentes = sum(c.cantidad * c.precio_unitario for c in self.componentes)
        if abs(total_componentes - self.costo_servicio) > 0.01:
            raise ValueError(
                "El costo_servicio debe coincidir con la sumatoria de cantidad × valor unitario "
                "de todos los insumos registrados."
            )
        return self

    model_config = ConfigDict(extra="forbid")


class MantenimientoUpdate(BaseModel):
    """
    Esquema para actualizar un mantenimiento existente.

    IMPORTANTE:
    - Todos los campos son opcionales
    - NO se puede cambiar el equipo (auditoría)
    - Solo se puede actualizar detalle y registrador

    Pydantic valida que solo estos campos permitidos se actualicen.
    """
    detalle_mantenimiento: Optional[str] = Field(
        None,
        max_length=1000,
        description="Actualizar descripción del trabajo (opcional)"
    )

    model_config = ConfigDict(extra="forbid")  # Rechaza campos no definidos


# ============================================================================
# ESQUEMAS DE RESPUESTA (SEGUROS)
# ============================================================================

class EquipoResumenMantenimiento(BaseModel):
    """Mini-esquema para resumen de equipo en respuesta de mantenimiento."""
    id: int
    codigo_activo: str
    modelo: str
    estado: str

    model_config = ConfigDict(from_attributes=True)


class UsuarioResumenMantenimiento(BaseModel):
    """Mini-esquema para resumen de usuario en respuesta de mantenimiento."""
    id: int
    nombre: str
    correo_institucional: str
    tipo_rol: str

    model_config = ConfigDict(from_attributes=True)


class TipoMantenimientoResponse(BaseModel):
    """Mini-esquema para tipo de mantenimiento en respuesta."""
    id: int
    nombre: str
    frecuencia_dias: Optional[int]

    model_config = ConfigDict(from_attributes=True)


class MantenimientoResponse(BaseModel):
    """
    Esquema para devolver datos de mantenimiento de forma segura.

    SIMPLIFICADO PARA BASE DE DATOS PLANA:
    - from_attributes=True: Permite crear desde objeto SQLAlchemy
    - Devuelve SOLO datos planos (IDs y valores directos)
    - SIN relaciones anidadas complejas que causen errores de validación
    - Campos exactamente como en la tabla de BD

    Auditoría:
    - Timestamps de creación para rastrabilidad
    - IDs de técnico, encargado, equipo y tipo para referencias
    """
    id: int = Field(..., description="Identificador único del registro")
    fecha_mantenimiento: date = Field(..., description="Fecha del mantenimiento (YYYY-MM-DD)")
    detalle_mantenimiento: Optional[str] = Field(None, description="Descripción del trabajo realizado")
    costo_servicio: float = Field(..., ge=0, description="Costo del servicio técnico en pesos")
    equipo_id: int = Field(..., gt=0, description="ID del equipo mantenido")
    encargado_id: int = Field(..., gt=0, description="ID del técnico que realizó el mantenimiento")
    tipo_mantenimiento_id: int = Field(..., gt=0, description="ID del tipo de mantenimiento")
    registrado_por: int = Field(..., gt=0, description="ID del usuario que registró el mantenimiento")
    created_at: datetime = Field(..., description="Timestamp de creación del registro")

    model_config = ConfigDict(from_attributes=True)


class InsumoGastadoResponse(BaseModel):
    """Insumo consumido en el mantenimiento para el calendario anual."""
    nombre: str = Field(..., description="Nombre del insumo")
    cantidad: float = Field(..., description="Cantidad utilizada")
    precio_unitario: float = Field(..., description="Valor unitario COP")
    subtotal: float = Field(..., description="cantidad x precio_unitario")

    model_config = ConfigDict(from_attributes=True)


class MantenimientoCalendarioResponse(MantenimientoResponse):
    """
    Respuesta enriquecida para la matriz 12x31 (/programacion).

    Incluye objetos anidados: técnico, observaciones, insumos y costo final.
    Hereda todos los campos planos para compatibilidad.
    """
    tecnico_nombre: str = Field(default="Sin asignar", description="Nombre completo del técnico")
    tipo_nombre: Optional[str] = Field(default=None, description="Nombre del tipo (Preventivo/Correctivo)")
    observaciones: Optional[str] = Field(default=None, description="Alias de detalle_mantenimiento")
    insumos_gastados: List[InsumoGastadoResponse] = Field(default_factory=list)
    costo_total: float = Field(default=0.0, description="Alias de costo_servicio")


class CerrarOrdenResponse(BaseModel):
    """Respuesta del triple disparo atómico: mantenimiento + programación + auditoría."""
    mantenimiento: MantenimientoResponse
    programacion_id: int
    programacion_estado: str
    auditoria_registros: int = Field(
        ...,
        description="Cantidad de filas insertadas en la bitácora de auditoría",
    )

    model_config = ConfigDict(from_attributes=True)


class MantenimientoHistorialEquipoResponse(BaseModel):
    """Resumen de mantenimiento para el historial en la hoja de vida del equipo."""
    id: int
    fecha_mantenimiento: date
    detalle_mantenimiento: Optional[str] = None
    tipo_nombre: Optional[str] = Field(None, description="Nombre del tipo (Preventivo, Correctivo, etc.)")
    tecnico_nombre: Optional[str] = Field(None, description="Nombre del técnico encargado")

    model_config = ConfigDict(from_attributes=True)


class MantenimientoListResponse(BaseModel):
    """
    Respuesta paginada de mantenimientos.

    Contiene múltiples registros con metadatos de paginación.
    """
    total: int = Field(..., description="Total de mantenimientos en la BD")
    page: int = Field(..., description="Número de página actual")
    size: int = Field(..., description="Cantidad de registros por página")
    items: list[MantenimientoResponse] = Field(
        ...,
        description="Lista de mantenimientos en esta página"
    )


class MantenimientoEstadisticas(BaseModel):
    """
    Esquema para estadísticas de mantenimiento.

    Usado en el dashboard de analítica para mostrar resumen de actividades.
    """
    total_mantenimientos: int = Field(..., description="Total de registros")
    mantenimientos_preventivos: int = Field(..., description="Mantenimientos preventivos")
    mantenimientos_correctivos: int = Field(..., description="Mantenimientos correctivos")
    porcentaje_preventivo: float = Field(..., description="% de mantenimientos preventivos")
    equipos_mantenidos: int = Field(..., description="Cantidad de equipos únicos mantenidos")
    promedio_por_equipo: float = Field(..., description="Promedio de mantenimientos por equipo")


"""
EJEMPLO DE USO EN ENDPOINTS:

```python
@router.post("/", response_model=MantenimientoResponse, status_code=201)
def crear_mantenimiento(
    mantenimiento_in: MantenimientoCreate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)  # Del JWT
):
    # El servicio valida existencia de FK, hashea si aplica, etc
    new_mant = mantenimiento_service.crear_mantenimiento(
        db, mantenimiento_in, usuario_actual.id
    )
    return new_mant  # FastAPI serializa con MantenimientoResponse
```
"""

