"""
Event Processor — intermediario entre acciones del sistema y la bitácora de negocio.

Regla de negocio: resuelve nombres y congela ubicaciones antes de persistir,
garantizando trazabilidad histórica inmutable.
"""

from __future__ import annotations

from typing import Optional, Tuple

from sqlalchemy.orm import Session, joinedload

from app.models.auditoria import Auditoria
from app.models.equipo import Equipo
from app.models.espacio import Espacio
from app.models.usuario import Usuario, TipoRol
from app.schemas.auditoria import (
    EventoAuditoriaCreate,
    EventoNarrativaMetadatos,
    TipoActorEnum,
    TipoEventoEnum,
    CategoriaEventoEnum,
)
from app.services.audit_narrator import audit_narrator


from app.services.audit_classifier import clasificar_categoria_evento, inferir_campo_crud


ROLES_SUPER_USUARIO = frozenset({
    TipoRol.JEFE_INFRAESTRUCTURA.value,
    TipoRol.AUXILIAR_INFRAESTRUCTURA.value,
    "Admin",
    "Administrador",
})

ETIQUETAS_ROL = {
    TipoRol.JEFE_INFRAESTRUCTURA.value: "Jefe de Infraestructura",
    TipoRol.AUXILIAR_INFRAESTRUCTURA.value: "Auxiliar de Infraestructura",
    TipoRol.TECNICO.value: "Técnico de Campo",
}

ETIQUETAS_EVENTO = {
    TipoEventoEnum.PROGRAMACION_MANTENIMIENTO: "Programación de mantenimiento",
    TipoEventoEnum.CRUD_EQUIPOS: "CRUD de equipos",
    TipoEventoEnum.CRUD_USUARIOS: "CRUD de usuarios",
    TipoEventoEnum.CRUD_TIPOS_EQUIPO: "CRUD de tipos de equipo",
    TipoEventoEnum.CRUD_TIPOS_MANTENIMIENTO: "CRUD de tipos de mantenimiento",
    TipoEventoEnum.CAMBIO_PERMISOS: "Cambio de permisos",
    TipoEventoEnum.CIERRE_ORDEN: "Programación de mantenimiento",
    TipoEventoEnum.CANCELACION: "Programación de mantenimiento",
    TipoEventoEnum.CAMBIO_ESTADO: "Programación de mantenimiento",
    TipoEventoEnum.CREACION: "Evento de gestión",
    TipoEventoEnum.REGISTRO_TECNICO: "Registro técnico",
    TipoEventoEnum.LEGACY: "Evento histórico",
}


def _nombre_completo_usuario(usuario: Optional[Usuario]) -> str:
    if not usuario:
        return "Usuario del sistema"
    return f"{usuario.nombre} {usuario.apellido}".strip()


def clasificar_actor(rol: Optional[str]) -> TipoActorEnum:
    """Regla de negocio: el patrón narrativo depende del rol del actor."""
    if rol in ROLES_SUPER_USUARIO:
        return TipoActorEnum.SUPER_USUARIO
    if rol == TipoRol.TECNICO.value:
        return TipoActorEnum.TECNICO
    return TipoActorEnum.DESCONOCIDO


def construir_ubicacion_snapshot(
    espacio_nombre: Optional[str],
    bloque_nombre: Optional[str],
    piso: Optional[int] = None,
) -> str:
    """
    Snapshot Policy: ubicación desglosada (bloque · piso · espacio).
    """
    bloque = (bloque_nombre or "").strip()
    salon = (espacio_nombre or "").strip()

    if not bloque and not salon and piso is None:
        return "Ubicación no registrada"

    partes = []
    if bloque:
        partes.append(bloque)
    if piso is not None:
        partes.append(f"Piso {piso}")
    if salon:
        partes.append(salon)

    return " · ".join(partes) if partes else "Ubicación no registrada"


def resolver_contexto_actor(
    db: Session,
    encargado_id: int,
) -> Tuple[str, str, TipoActorEnum]:
    """Context lookup: traduce el ID del operario a nombre y rol legibles."""
    usuario = db.query(Usuario).filter(Usuario.id == encargado_id).first()
    nombre = _nombre_completo_usuario(usuario)
    rol = usuario.tipo_rol if usuario else "Desconocido"
    etiqueta = ETIQUETAS_ROL.get(rol, rol)
    return nombre, etiqueta, clasificar_actor(rol)


def resolver_contexto_equipo(
    db: Session,
    equipo_id: Optional[int],
) -> Tuple[str, str]:
    """Context lookup: obtiene descripción del activo y snapshot de ubicación."""
    if not equipo_id:
        return "Recurso no especificado", "Ubicación no registrada"

    equipo = (
        db.query(Equipo)
        .options(
            joinedload(Equipo.espacio).joinedload(Espacio.bloque),
            joinedload(Equipo.marca),
        )
        .filter(Equipo.id == equipo_id)
        .first()
    )
    if not equipo:
        return f"Equipo #{equipo_id}", "Ubicación no registrada"

    marca = equipo.marca.nombre if equipo.marca else ""
    modelo = equipo.modelo or ""
    descripcion_recurso = equipo.codigo_activo
    if marca or modelo:
        descripcion_recurso = f"{equipo.codigo_activo} ({marca} {modelo})".strip()

    espacio = equipo.espacio
    ubicacion = construir_ubicacion_snapshot(
        espacio.nombre if espacio else None,
        espacio.bloque.nombre_bloque if espacio and espacio.bloque else None,
        espacio.piso if espacio else None,
    )
    return descripcion_recurso.strip(), ubicacion


def _campo_tecnico_por_evento(evento: EventoAuditoriaCreate) -> str:
    if evento.campo:
        return evento.campo
    if evento.tipo_evento == TipoEventoEnum.CIERRE_ORDEN:
        return "cierre_orden"
    if evento.tipo_evento == TipoEventoEnum.CANCELACION:
        return "cancelacion"
    return "estado"


def _categoria_persistida(evento: EventoAuditoriaCreate) -> str:
    """Resuelve la categoría final almacenada en tipo_evento."""
    valor = evento.tipo_evento.value
    categorias_negocio = {c.value for c in CategoriaEventoEnum}  # type: ignore[name-defined]
    if valor in categorias_negocio:
        return valor
    return clasificar_categoria_evento(evento.tabla_afectada, _campo_tecnico_por_evento(evento))


def procesar_evento_auditoria(
    db: Session,
    evento: EventoAuditoriaCreate,
    *,
    flush: bool = False,
) -> Auditoria:
    """
    Event Processor: valida, resuelve contexto, narra y persiste el evento.

    Regla de negocio: ningún INSERT directo a auditoría debe omitir este intermediario.
    """
    actor_nombre, actor_rol_etiqueta, tipo_actor = resolver_contexto_actor(
        db, evento.encargado_id
    )

    recurso_resuelto, ubicacion_resuelta = resolver_contexto_equipo(db, evento.equipo_id)
    recurso = evento.recurso_descripcion or recurso_resuelto
    ubicacion = evento.ubicacion_snapshot or ubicacion_resuelta

    metadatos = EventoNarrativaMetadatos(
        tipo_actor=tipo_actor,
        tipo_evento=evento.tipo_evento,
        actor_nombre=actor_nombre,
        actor_rol_etiqueta=actor_rol_etiqueta,
        recurso_descripcion=recurso,
        ubicacion_snapshot=ubicacion,
        estado_anterior=evento.estado_anterior,
        estado_nuevo=evento.estado_nuevo,
        justificacion=evento.justificacion,
        detalle_operativo=evento.detalle_operativo,
    )
    narrativa = audit_narrator(metadatos)
    categoria = _categoria_persistida(evento)

    registro = Auditoria(
        tabla_afectada=evento.tabla_afectada,
        registro_id=evento.registro_id,
        campo=_campo_tecnico_por_evento(evento),
        valor_anterior=evento.estado_anterior,
        valor_nuevo=evento.estado_nuevo,
        encargado_id=evento.encargado_id,
        tipo_evento=categoria,
        actor_nombre=actor_nombre,
        actor_rol=tipo_actor.value,
        actor_rol_etiqueta=actor_rol_etiqueta,
        ubicacion_snapshot=ubicacion,
        recurso_descripcion=recurso,
        narrativa=narrativa,
        justificacion=evento.justificacion,
    )

    db.add(registro)
    if flush:
        db.flush()

    return registro


def registrar_evento_crud(
    db: Session,
    *,
    tabla_afectada: str,
    registro_id: int,
    encargado_id: int,
    accion: str,
    valor_anterior: Optional[str] = None,
    valor_nuevo: Optional[str] = None,
    equipo_id: Optional[int] = None,
    recurso_descripcion: Optional[str] = None,
    flush: bool = False,
) -> Auditoria:
    """Registra un evento CRUD con categoría automática según tabla y acción."""
    campo = inferir_campo_crud(accion)
    categoria = clasificar_categoria_evento(tabla_afectada, campo)

    tipo_map = {
        CategoriaEventoEnum.PROGRAMACION_MANTENIMIENTO.value: TipoEventoEnum.PROGRAMACION_MANTENIMIENTO,
        CategoriaEventoEnum.CRUD_EQUIPOS.value: TipoEventoEnum.CRUD_EQUIPOS,
        CategoriaEventoEnum.CRUD_USUARIOS.value: TipoEventoEnum.CRUD_USUARIOS,
        CategoriaEventoEnum.CRUD_TIPOS_EQUIPO.value: TipoEventoEnum.CRUD_TIPOS_EQUIPO,
        CategoriaEventoEnum.CRUD_TIPOS_MANTENIMIENTO.value: TipoEventoEnum.CRUD_TIPOS_MANTENIMIENTO,
        CategoriaEventoEnum.CAMBIO_PERMISOS.value: TipoEventoEnum.CAMBIO_PERMISOS,
    }
    tipo_evento = tipo_map.get(categoria, TipoEventoEnum.PROGRAMACION_MANTENIMIENTO)

    return procesar_evento_auditoria(
        db,
        EventoAuditoriaCreate(
            tipo_evento=tipo_evento,
            encargado_id=encargado_id,
            registro_id=registro_id,
            tabla_afectada=tabla_afectada,
            campo=campo,
            estado_anterior=valor_anterior,
            estado_nuevo=valor_nuevo,
            equipo_id=equipo_id,
            recurso_descripcion=recurso_descripcion,
        ),
        flush=flush,
    )
