"""
Clasificación automática de categorías para la bitácora de gestión.

Regla de negocio: la categoría se determina por tabla afectada y campo modificado
en el momento de registrar el evento.
"""

from __future__ import annotations

from app.schemas.auditoria import CategoriaEventoEnum


def clasificar_categoria_evento(tabla_afectada: str, campo: str = "") -> str:
    """
    Devuelve la categoría legible que se persiste en auditoria.tipo_evento.
    """
    tabla = (tabla_afectada or "").strip().lower()
    campo_norm = (campo or "").strip().lower()

    if tabla == "programaciones":
        return CategoriaEventoEnum.PROGRAMACION_MANTENIMIENTO.value
    if tabla == "equipos":
        return CategoriaEventoEnum.CRUD_EQUIPOS.value
    if tabla == "tipos_equipos":
        return CategoriaEventoEnum.CRUD_TIPOS_EQUIPO.value
    if tabla == "tipos_mantenimiento":
        return CategoriaEventoEnum.CRUD_TIPOS_MANTENIMIENTO.value
    if tabla == "encargados":
        if campo_norm in {"tipo_rol", "rol", "activo"}:
            return CategoriaEventoEnum.CAMBIO_PERMISOS.value
        return CategoriaEventoEnum.CRUD_USUARIOS.value

    return CategoriaEventoEnum.PROGRAMACION_MANTENIMIENTO.value


def inferir_campo_crud(accion: str) -> str:
    """Nombre técnico del campo según la operación CRUD."""
    accion_norm = (accion or "").strip().lower()
    if accion_norm in {"insert", "create", "creacion"}:
        return "creacion"
    if accion_norm in {"update", "edit", "edicion"}:
        return "edicion"
    if accion_norm in {"delete", "eliminacion"}:
        return "eliminacion"
    return accion_norm or "operacion"
