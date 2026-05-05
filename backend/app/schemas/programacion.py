"""
Esquemas Pydantic para la entidad Programación de Mantenimiento.

Este módulo define los contratos de validación de datos para:
- Creación de programaciones de mantenimiento
- Actualización de programaciones (cambios de estado, observaciones, etc)
- Respuestas seguras con información de relaciones (equipo, encargado, tipo)
- Enumeraciones de estados de programación

Arquitectura:
- Validación estricta con Pydantic v2
- Tipos anidados para relaciones (equipo, usuario, tipo mantenimiento)
- Timestamps automáticos de BD (no cliente)
- Documentación completa con ejemplos
- Validación de IDs mayores a cero para integridad referencial
"""

from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


# ============================================================================
# ENUMS Y CONSTANTES
# ============================================================================

class EstadoProgramacionEnum(str, Enum):
    """Estados posibles de una programación de mantenimiento."""
    PENDIENTE = "Pendiente"
    COMPLETADO = "Completado"
    CANCELADO = "Cancelado"
    VENCIDO = "Vencido"


# ============================================================================
# ESQUEMAS BASE Y CREATE
# ============================================================================

class ProgramacionBase(BaseModel):
    """
    Esquema base con campos comunes de programación de mantenimiento.

    Contiene los atributos esenciales compartidos entre creación y respuesta.
    """
    fecha_programada: date = Field(
        ...,
        description="Fecha programada para ejecutar el mantenimiento (YYYY-MM-DD)"
    )
    equipo_id: int = Field(
        ...,
        gt=0,
        description="ID del equipo a mantener (debe existir en BD)"
    )
    encargado_id: int = Field(
        ...,
        gt=0,
        description="ID del técnico responsable de ejecutar el mantenimiento"
    )
    tipo_mantenimiento_id: int = Field(
        ...,
        gt=0,
        description="ID del tipo de mantenimiento (Preventivo, Correctivo, Inspección)"
    )


class ProgramacionCreate(ProgramacionBase):
    """
    Esquema para creación de nueva programación de mantenimiento.

    Validación Pydantic:
    - Todos los IDs foráneos deben ser positivos (gt=0)
    - La fecha debe ser válida y de tipo date
    - Las observaciones son opcionales
    - El estado inicial se establece en BD (no en cliente)

    Nota: El estado inicial es "Pendiente" y se asigna automáticamente
    en el modelo de base de datos (no acepta estado en POST).
    """
    observaciones: Optional[str] = Field(
        None,
        max_length=1000,
        description="Observaciones adicionales sobre la programación (opcional, máximo 1000 caracteres)"
    )


class ProgramacionUpdate(BaseModel):
    """
    Esquema para actualizar una programación existente.

    IMPORTANTE:
    - Todos los campos son opcionales
    - Permite cambiar el estado de la programación
    - Permite actualizar el ID de tipo de mantenimiento
    - La fecha programada puede ser modificada si aún no se ha completado

    Pydantic valida que solo estos campos permitidos se actualicen.
    Se recomienda usar ConfigDict(extra="forbid") para rechazar campos inesperados.
    """
    fecha_programada: Optional[date] = Field(
        None,
        description="Actualizar fecha programada (opcional)"
    )
    estado: Optional[EstadoProgramacionEnum] = Field(
        None,
        description="Cambiar estado: Pendiente, Completado, Cancelado, Vencido (opcional)"
    )
    encargado_id: Optional[int] = Field(
        None,
        gt=0,
        description="ID del técnico responsable (opcional, debe ser > 0)"
    )
    tipo_mantenimiento_id: Optional[int] = Field(
        None,
        gt=0,
        description="ID del tipo de mantenimiento (opcional, debe ser > 0)"
    )
    mantenimiento_id: Optional[int] = Field(
        None,
        gt=0,
        description="ID del mantenimiento asociado (opcional, debe ser > 0)"
    )
    observaciones: Optional[str] = Field(
        None,
        max_length=1000,
        description="Actualizar observaciones (opcional, máximo 1000 caracteres)"
    )

    model_config = ConfigDict(extra="forbid")  # Rechaza campos no definidos


# ============================================================================
# ESQUEMAS DE RESPUESTA (SEGUROS)
# ============================================================================

class EquipoResumenProgramacion(BaseModel):
    """Mini-esquema para resumen de equipo en respuesta de programación."""
    id: int
    codigo_activo: str
    modelo: str
    estado: str

    model_config = ConfigDict(from_attributes=True)


class UsuarioResumenProgramacion(BaseModel):
    """Mini-esquema para resumen de usuario en respuesta de programación."""
    id: int
    nombre: str
    correo_institucional: str
    tipo_rol: str

    model_config = ConfigDict(from_attributes=True)


class TipoMantenimientoProgramacion(BaseModel):
    """Mini-esquema para tipo de mantenimiento en respuesta de programación."""
    id: int
    nombre: str
    frecuencia_dias: Optional[int]

    model_config = ConfigDict(from_attributes=True)


class MantenimientoResumenProgramacion(BaseModel):
    """Mini-esquema para mantenimiento asociado en respuesta de programación."""
    id: int
    detalle_mantenimiento: Optional[str]
    fecha_mantenimiento: date

    model_config = ConfigDict(from_attributes=True)


class ProgramacionResponse(ProgramacionBase):
    """
    Esquema para devolver datos de programación de forma segura.

    Seguridad Crítica:
    - from_attributes=True: Permite crear desde objeto SQLAlchemy ORM
    - NO incluye datos sensibles
    - Solo devuelve campos "públicos"
    - Incluye relaciones anidadas con mini-esquemas (equipo, técnico, tipo)

    Auditoría y Trazabilidad:
    - Timestamps de creación y actualización
    - Estado actual de la programación
    - Información sobre el equipo y responsables

    Estructura:
    - Hereda campos de ProgramacionBase
    - Agrega id, estado, relaciones anidadas y timestamps
    """
    id: int = Field(..., description="Identificador único de la programación")
    estado: EstadoProgramacionEnum = Field(
        ...,
        description="Estado actual: Pendiente, Completado, Cancelado, Vencido"
    )
    equipo: Optional[EquipoResumenProgramacion] = Field(
        None,
        description="Información resumida del equipo programado"
    )
    encargado: Optional[UsuarioResumenProgramacion] = Field(
        None,
        description="Información resumida del técnico responsable"
    )
    tipo_mantenimiento: Optional[TipoMantenimientoProgramacion] = Field(
        None,
        description="Información resumida del tipo de mantenimiento"
    )
    mantenimiento: Optional[MantenimientoResumenProgramacion] = Field(
        None,
        description="Información resumida del mantenimiento realizado (si aplica)"
    )
    observaciones: Optional[str] = Field(
        None,
        description="Observaciones registradas en la programación"
    )
    created_at: datetime = Field(..., description="Timestamp de creación del registro")
    updated_at: datetime = Field(..., description="Timestamp de última actualización")

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# ESQUEMAS DE RESPUESTA PAGINADA
# ============================================================================

class ProgramacionListResponse(BaseModel):
    """
    Respuesta paginada de programaciones de mantenimiento.

    Contiene múltiples registros de programaciones con metadatos de paginación.
    Utilizado para endpoints GET /programaciones/ con soporte de pagination.
    """
    total: int = Field(..., description="Total de programaciones en la BD")
    page: int = Field(..., description="Número de página actual")
    size: int = Field(..., description="Cantidad de registros por página")
    items: list[ProgramacionResponse] = Field(
        ...,
        description="Lista de programaciones en esta página"
    )


# ============================================================================
# ESQUEMAS PARA ESTADÍSTICAS Y ANÁLISIS
# ============================================================================

class ProgramacionEstadisticas(BaseModel):
    """
    Esquema para estadísticas de programación de mantenimiento.

    Usado en dashboards de analítica para mostrar resumen de programaciones,
    distribución de estados y métricas de cumplimiento.
    """
    total_programaciones: int = Field(
        ...,
        description="Total de programaciones registradas"
    )
    pendientes: int = Field(
        ...,
        description="Cantidad de programaciones en estado Pendiente"
    )
    completadas: int = Field(
        ...,
        description="Cantidad de programaciones completadas"
    )
    canceladas: int = Field(
        ...,
        description="Cantidad de programaciones canceladas"
    )
    vencidas: int = Field(
        ...,
        description="Cantidad de programaciones vencidas"
    )
    porcentaje_completitud: float = Field(
        ...,
        description="Porcentaje de programaciones completadas vs total"
    )
    equipos_con_programacion: int = Field(
        ...,
        description="Cantidad de equipos con al menos una programación"
    )

class ProgramacionesPorEstado(BaseModel):
    """Agrupación de programaciones por su estado actual"""
    pendientes: list[ProgramacionResponse]
    completadas: list[ProgramacionResponse]
    canceladas: list[ProgramacionResponse]
    vencidas: list[ProgramacionResponse]

class ProgramacionResumenAnalytica(BaseModel):
    """Resumen de métricas para el dashboard de programaciones"""
    total_programaciones: int
    programaciones_pendientes: int
    programaciones_vencidas: int
    porcentaje_cumplimiento: float
    proxima_fecha_programada: Optional[date] = None
    equipo_mas_frecuente: Optional[str] = None

# ============================================================================
# DOCUMENTACIÓN DE EJEMPLO
# ============================================================================

"""
EJEMPLO DE USO EN ENDPOINTS:

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.programacion import (
    ProgramacionCreate,
    ProgramacionUpdate,
    ProgramacionResponse,
    ProgramacionListResponse,
)
from app.services import programacion_service
from app.db.session import get_db

router = APIRouter(prefix="/programaciones", tags=["Programaciones"])

# ============================================================================
# CREATE - Crear nueva programación
# ============================================================================
@router.post(
    "/",
    response_model=ProgramacionResponse,
    status_code=status.HTTP_201_CREATED
)
def crear_programacion(
    programacion_in: ProgramacionCreate,
    db: Session = Depends(get_db),
    usuario_actual = Depends(obtener_usuario_actual)
):
    '''
    Crea una nueva programación de mantenimiento.
    
    Estados iniciales:
    - Estado: "Pendiente"
    - Creado por: Usuario autenticado
    - Timestamp: Auto-asignado por BD
    '''
    return programacion_service.crear_programacion(
        db, programacion_in, usuario_actual.id
    )

# ============================================================================
# READ - Obtener una programación específica
# ============================================================================
@router.get("/{id_programacion}", response_model=ProgramacionResponse)
def obtener_programacion(
    id_programacion: int,
    db: Session = Depends(get_db)
):
    '''Obtiene una programación específica por ID'''
    programacion = programacion_service.obtener_por_id(db, id_programacion)
    if not programacion:
        raise HTTPException(status_code=404, detail="Programación no encontrada")
    return programacion

# ============================================================================
# LIST - Listar con paginación
# ============================================================================
@router.get("/", response_model=ProgramacionListResponse)
def listar_programaciones(
    page: int = 1,
    size: int = 10,
    estado: Optional[str] = None,
    db: Session = Depends(get_db)
):
    '''
    Lista programaciones con paginación.
    
    Parámetros opcionales:
    - estado: Filtrar por estado (Pendiente, Completado, Cancelado, Vencido)
    '''
    return programacion_service.listar_con_filtros(
        db, page, size, estado=estado
    )

# ============================================================================
# UPDATE - Actualizar programación existente
# ============================================================================
@router.patch("/{id_programacion}", response_model=ProgramacionResponse)
def actualizar_programacion(
    id_programacion: int,
    programacion_in: ProgramacionUpdate,
    db: Session = Depends(get_db),
    usuario_actual = Depends(obtener_usuario_actual)
):
    '''
    Actualiza una programación existente.
    
    Campos actualizables:
    - fecha_programada, estado, encargado_id
    - tipo_mantenimiento_id, mantenimiento_id, observaciones
    '''
    programacion = programacion_service.actualizar(
        db, id_programacion, programacion_in, usuario_actual.id
    )
    if not programacion:
        raise HTTPException(status_code=404, detail="Programación no encontrada")
    return programacion

# ============================================================================
# DELETE - Eliminar programación
# ============================================================================
@router.delete("/{id_programacion}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_programacion(
    id_programacion: int,
    db: Session = Depends(get_db),
    usuario_actual = Depends(obtener_usuario_actual)
):
    '''Elimina una programación (generalmente soft-delete en BD)'''
    success = programacion_service.eliminar(
        db, id_programacion, usuario_actual.id
    )
    if not success:
        raise HTTPException(status_code=404, detail="Programación no encontrada")
    return None
```

VALIDACIÓN DE CAMPOS:

- `fecha_programada`: Tipo date, requerido. Formato: YYYY-MM-DD
- `equipo_id`: int > 0, requerido. Valida existencia en FK
- `encargado_id`: int > 0, requerido. Debe ser usuario técnico
- `tipo_mantenimiento_id`: int > 0, requerido. Valida existencia
- `observaciones`: str, opcional, máximo 1000 caracteres
- `estado`: Solo en Update/Response. Valores: Pendiente, Completado, Cancelado, Vencido
- `mantenimiento_id`: int > 0, opcional. Para vincular a mantenimiento realizado

INTEGRIDAD REFERENCIAL:

La validación de IDs mayores a cero (gt=0) asegura:
1. No permite valores nulos o cero
2. No permite valores negativos
3. La existencia real se valida en la capa de servicios con ForeignKey

EJEMPLO DE REQUEST:

POST /api/v1/programaciones/
{
    "fecha_programada": "2026-06-15",
    "equipo_id": 5,
    "encargado_id": 3,
    "tipo_mantenimiento_id": 1,
    "observaciones": "Revisar los componentes críticos y cambiar aceite"
}

EJEMPLO DE RESPONSE (201 Created):

{
    "id": 42,
    "fecha_programada": "2026-06-15",
    "estado": "Pendiente",
    "equipo_id": 5,
    "encargado_id": 3,
    "tipo_mantenimiento_id": 1,
    "observaciones": "Revisar los componentes críticos y cambiar aceite",
    "equipo": {
        "id": 5,
        "codigo_activo": "EQ-0005",
        "modelo": "Compresor Atlas Copco",
        "estado": "Operativo"
    },
    "encargado": {
        "id": 3,
        "nombre": "Juan García López",
        "correo_institucional": "juan.garcia@ucc.edu.co",
        "tipo_rol": "Tecnico interno"
    },
    "tipo_mantenimiento": {
        "id": 1,
        "nombre": "Preventivo",
        "frecuencia_dias": 30
    },
    "mantenimiento": null,
    "created_at": "2026-05-05T10:30:45.123456",
    "updated_at": "2026-05-05T10:30:45.123456"
}

EJEMPLO DE UPDATE:

PATCH /api/v1/programaciones/42
{
    "estado": "Completado",
    "mantenimiento_id": 15,
    "observaciones": "Mantenimiento completado exitosamente"
}
"""
