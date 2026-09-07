"""
Mapeo de registros de auditoría a DTOs de presentación para la bitácora.

Regla de negocio: toda formateación de fecha y redacción ocurre aquí, no en el frontend.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Optional

from app.models.auditoria import Auditoria
from app.schemas.auditoria import (
    EventoGestionPresentacion,
    EventoNarrativaMetadatos,
    TipoActorEnum,
    TipoEventoEnum,
    CategoriaEventoEnum,
)
from app.services.audit_event_processor import ETIQUETAS_EVENTO, ETIQUETAS_ROL
from app.services.audit_narrator import audit_narrator

try:
    from zoneinfo import ZoneInfo
    ZONA_COLOMBIA = ZoneInfo("America/Bogota")
except Exception:
    ZONA_COLOMBIA = timezone(timedelta(hours=-5))

MESES_ES = (
    "ene", "feb", "mar", "abr", "may", "jun",
    "jul", "ago", "sep", "oct", "nov", "dic",
)

MAPEO_LEGACY_TIPO = {
    "cierre_orden": CategoriaEventoEnum.PROGRAMACION_MANTENIMIENTO.value,
    "cancelacion": CategoriaEventoEnum.PROGRAMACION_MANTENIMIENTO.value,
    "cambio_estado": CategoriaEventoEnum.PROGRAMACION_MANTENIMIENTO.value,
    "programaciones": CategoriaEventoEnum.PROGRAMACION_MANTENIMIENTO.value,
}


def formatear_fecha_hora_bitacora(fecha: Optional[datetime]) -> str:
    """Formato único de fecha/hora para toda la bitácora de gestión."""
    if not fecha:
        return "Fecha no registrada"

    if fecha.tzinfo is None:
        fecha = fecha.replace(tzinfo=ZONA_COLOMBIA)
    else:
        fecha = fecha.astimezone(ZONA_COLOMBIA)

    mes = MESES_ES[fecha.month - 1]
    return f"{fecha.day:02d} {mes} {fecha.year} · {fecha.hour:02d}:{fecha.minute:02d}"


def _resolver_nombre_actor(registro: Auditoria) -> str:
    if registro.actor_nombre:
        return registro.actor_nombre.strip()
    encargado = registro.encargado
    if encargado:
        return f"{encargado.nombre} {encargado.apellido}".strip()
    return "Responsable no registrado"


def _etiqueta_tipo_evento(registro: Auditoria) -> str:
    valor = (registro.tipo_evento or "").strip()
    if valor in {c.value for c in CategoriaEventoEnum}:
        return valor
    if valor in MAPEO_LEGACY_TIPO:
        return MAPEO_LEGACY_TIPO[valor]
    if registro.tabla_afectada == "programaciones":
        return CategoriaEventoEnum.PROGRAMACION_MANTENIMIENTO.value
    try:
        enum_val = TipoEventoEnum(valor)
        return ETIQUETAS_EVENTO.get(enum_val, valor or "Evento de gestión")
    except ValueError:
        return valor or "Evento de gestión"


def _tipo_evento_desde_registro(registro: Auditoria) -> TipoEventoEnum:
    valor = registro.tipo_evento
    if valor:
        try:
            return TipoEventoEnum(valor)
        except ValueError:
            for cat in CategoriaEventoEnum:
                if cat.value == valor:
                    return TipoEventoEnum(cat.value)
    return TipoEventoEnum.LEGACY


def _tipo_actor_desde_registro(registro: Auditoria) -> TipoActorEnum:
    if registro.actor_rol:
        try:
            return TipoActorEnum(registro.actor_rol)
        except ValueError:
            pass
    return TipoActorEnum.DESCONOCIDO


def _ubicacion_desde_registro(registro: Auditoria) -> str:
    ubicacion = (registro.ubicacion_snapshot or "").strip()
    return ubicacion if ubicacion else "Ubicación no registrada"


def _narrativa_desde_registro(registro: Auditoria) -> str:
    if registro.narrativa:
        return registro.narrativa

    meta = EventoNarrativaMetadatos(
        tipo_actor=_tipo_actor_desde_registro(registro),
        tipo_evento=_tipo_evento_desde_registro(registro),
        actor_nombre=_resolver_nombre_actor(registro),
        actor_rol_etiqueta=registro.actor_rol_etiqueta or "Operario",
        recurso_descripcion=registro.recurso_descripcion or f"Registro #{registro.registro_id}",
        ubicacion_snapshot=_ubicacion_desde_registro(registro),
        estado_anterior=registro.valor_anterior,
        estado_nuevo=registro.valor_nuevo,
        justificacion=registro.justificacion,
        tabla_tecnica=registro.tabla_afectada,
        campo_tecnico=registro.campo,
    )
    return audit_narrator(meta)


def a_evento_presentacion(registro: Auditoria) -> EventoGestionPresentacion:
    """Convierte un registro ORM en DTO listo para la UI."""
    return EventoGestionPresentacion(
        id=registro.id,
        fecha_hora=formatear_fecha_hora_bitacora(registro.fecha_cambio),
        actor_nombre=_resolver_nombre_actor(registro),
        actor_rol_etiqueta=registro.actor_rol_etiqueta or ETIQUETAS_ROL.get("Tecnico", "Operario"),
        ubicacion=_ubicacion_desde_registro(registro),
        narrativa=_narrativa_desde_registro(registro),
        tipo_evento_etiqueta=_etiqueta_tipo_evento(registro),
    )
