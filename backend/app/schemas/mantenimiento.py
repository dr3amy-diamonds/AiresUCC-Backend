"""
Esquemas Pydantic para la entidad Mantenimiento.

Este módulo define los contratos de validación de datos para:
- Creación de registros de mantenimiento
- Actualización de datos de mantenimiento
- Respuestas seguras (auditoría y trazabilidad)
- Enumeraciones de estados de mantenimiento

Arquitectura:
- Validación estricta con Pydantic v2
- Tipos anidados para relaciones (técnico, equipo, tipo)
- Timestamps automáticos de BD (no cliente)
- Documentación completa con ejemplos
"""

from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


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


class MantenimientoResponse(MantenimientoBase):
    """
    Esquema para devolver datos de mantenimiento de forma segura.

    Seguridad Crítica:
    - from_attributes=True: Permite crear desde objeto SQLAlchemy
    - NO incluye datos sensibles
    - Solo devuelve campos "públicos"
    - Incluye relaciones anidadas (equipo, técnico, tipo)

    Auditoría:
    - Timestamps de creación para rastrabilidad
    - IDs de técnico y registrador para auditoría
    """
    id: int = Field(..., description="Identificador único del registro")
    fecha_mantenimiento: date
    equipo: Optional[EquipoResumenMantenimiento]
    encargado: Optional[UsuarioResumenMantenimiento]
    tipo_mantenimiento: Optional[TipoMantenimientoResponse]
    registrador: Optional[UsuarioResumenMantenimiento]
    created_at: datetime = Field(..., description="Timestamp de creación del registro")

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

