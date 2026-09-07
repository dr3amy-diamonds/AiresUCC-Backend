"""
Traductor de eventos de gestión a narrativa humana.

Regla de negocio: la bitácora debe leerse como un relato, no como un diff técnico.
Esta capa es pura (sin BD) para garantizar resiliencia ante datos incompletos.
"""

from __future__ import annotations

from typing import Optional

from app.schemas.auditoria import EventoNarrativaMetadatos, TipoActorEnum, TipoEventoEnum


def _valor_seguro(valor: Optional[str], alterno: str = "información no disponible") -> str:
    """Evita narrativas rotas cuando falta un dato puntual del contexto."""
    texto = (valor or "").strip()
    return texto if texto else alterno


def _narrativa_super_usuario(meta: EventoNarrativaMetadatos) -> str:
    """
    Regla de negocio: acciones administrativas siempre exponen recurso, ubicación y motivo.
    """
    actor = _valor_seguro(meta.actor_nombre, "un administrador del sistema")
    rol = _valor_seguro(meta.actor_rol_etiqueta, "Administrador")
    recurso = _valor_seguro(meta.recurso_descripcion, "un recurso del sistema")
    ubicacion = _valor_seguro(meta.ubicacion_snapshot, "ubicación no registrada")
    justificacion = _valor_seguro(meta.justificacion, "sin motivo registrado")

    if meta.tipo_evento == TipoEventoEnum.CANCELACION:
        accion = "canceló la orden de trabajo"
    elif meta.tipo_evento == TipoEventoEnum.CAMBIO_ESTADO:
        accion = f"actualizó el estado de {recurso}"
    elif meta.tipo_evento == TipoEventoEnum.CREACION:
        accion = "registró un nuevo elemento en el sistema sobre"
    else:
        accion = "realizó una acción administrativa sobre"

    transicion = ""
    if meta.estado_anterior and meta.estado_nuevo:
        transicion = (
            f" El estado cambió de «{_valor_seguro(meta.estado_anterior)}» "
            f"a «{_valor_seguro(meta.estado_nuevo)}»."
        )

    return (
        f"El {rol} {actor} {accion} {recurso} en {ubicacion}.{transicion} "
        f"Justificación registrada: «{justificacion}»."
    )


def _narrativa_tecnico(meta: EventoNarrativaMetadatos) -> str:
    """
    Regla de negocio: el flujo operativo prioriza equipo, ubicación y resultado del servicio.
    """
    actor = _valor_seguro(meta.actor_nombre, "un técnico de infraestructura")
    recurso = _valor_seguro(meta.recurso_descripcion, "un equipo de climatización")
    ubicacion = _valor_seguro(meta.ubicacion_snapshot, "ubicación no registrada")

    if meta.tipo_evento == TipoEventoEnum.CIERRE_ORDEN:
        transicion = ""
        if meta.estado_anterior and meta.estado_nuevo:
            transicion = (
                f" La orden pasó de «{_valor_seguro(meta.estado_anterior)}» "
                f"a «{_valor_seguro(meta.estado_nuevo)}»."
            )
        detalle = _valor_seguro(
            meta.detalle_operativo,
            "Se registró el reporte técnico correspondiente.",
        )
        return (
            f"El técnico {actor} completó el mantenimiento del equipo {recurso} "
            f"ubicado en {ubicacion}.{transicion} {detalle}"
        )

    if meta.tipo_evento == TipoEventoEnum.CAMBIO_ESTADO:
        return (
            f"El técnico {actor} actualizó el estado operativo de {recurso} "
            f"en {ubicacion}, de «{_valor_seguro(meta.estado_anterior)}» "
            f"a «{_valor_seguro(meta.estado_nuevo)}»."
        )

    detalle = _valor_seguro(meta.detalle_operativo, "Intervención registrada en campo.")
    return (
        f"El técnico {actor} atendió el equipo {recurso} en {ubicacion}. {detalle}"
    )


def _narrativa_legacy(meta: EventoNarrativaMetadatos) -> str:
    """Fallback para registros históricos sin metadatos de negocio completos."""
    actor = _valor_seguro(meta.actor_nombre, "un usuario del sistema")
    campo = _valor_seguro(meta.campo_tecnico, "un campo")
    tabla = _valor_seguro(meta.tabla_tecnica, "una tabla")
    anterior = _valor_seguro(meta.estado_anterior, "(vacío)")
    nuevo = _valor_seguro(meta.estado_nuevo, "(vacío)")
    return (
        f"{actor} modificó {campo} en {tabla}. "
        f"El valor cambió de «{anterior}» a «{nuevo}»."
    )


def audit_narrator(meta: EventoNarrativaMetadatos) -> str:
    """
    Orquestador: elige el patrón narrativo según el actor y el tipo de evento.

    Regla de negocio: un solo punto de redacción evita inconsistencias entre API y UI.
    """
    if meta.tipo_actor == TipoActorEnum.SUPER_USUARIO:
        return _narrativa_super_usuario(meta)

    if meta.tipo_actor == TipoActorEnum.TECNICO:
        return _narrativa_tecnico(meta)

    return _narrativa_legacy(meta)
