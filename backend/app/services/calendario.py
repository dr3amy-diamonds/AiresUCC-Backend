"""
Servicio de agregación para el Resumen Anual (/calendario).

Un solo llamado reemplaza ~40 requests paginados del frontend legacy:
  espacios + mantenimientos(anio) + programaciones Completadas(anio)

Estrategia:
- 1 query Espacios con bloque (filas).
- 1 query Mantenimientos del año con eager loads (detalle modal).
- 1 query Programaciones Completadas del año (detalle modal).
- 2 queries GROUP BY (espacio, mes, día) para celdas pre-agregadas.
- Merge en Python para totales por espacio / por mes.
"""

from collections import defaultdict
from typing import Dict, List, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.models.espacio import Espacio
from app.models.equipo import Equipo
from app.models.mantenimiento import Mantenimiento
from app.models.programacion import Programacion
from app.models.componente_usado import ComponenteUsado
from app.schemas.programacion import EstadoProgramacionEnum


def _nombre_tecnico(usuario) -> str:
    if not usuario:
        return "Sin asignar"
    nombre = getattr(usuario, "nombre", None)
    apellido = getattr(usuario, "apellido", None)
    if nombre and apellido:
        return f"{nombre} {apellido}".strip()
    if nombre:
        return str(nombre)
    correo = getattr(usuario, "correo_institucional", None)
    return str(correo) if correo else "Sin asignar"


def _celdas_groupby(
    db: Session, anio: int
) -> Dict[Tuple[int, int, int], Dict]:
    """GROUP BY real en BD: (espacio_id, mes, día) -> {conteo, orden_ids}."""
    agrupado: Dict[Tuple[int, int, int], Dict] = {}

    # Mantenimientos agrupados vía equipo -> espacio
    try:
        filas_mnt = (
            db.query(
                Espacio.id.label("espacio_id"),
                func.date_part("month", Mantenimiento.fecha_mantenimiento).label("mes"),
                func.date_part("day", Mantenimiento.fecha_mantenimiento).label("dia"),
                func.count(Mantenimiento.id).label("conteo"),
            )
            .join(Equipo, Equipo.id == Mantenimiento.equipo_id)
            .join(Espacio, Espacio.id == Equipo.espacio_id)
            .filter(func.date_part("year", Mantenimiento.fecha_mantenimiento) == anio)
            .group_by(
                Espacio.id,
                func.date_part("month", Mantenimiento.fecha_mantenimiento),
                func.date_part("day", Mantenimiento.fecha_mantenimiento),
            )
            .all()
        )
        for f in filas_mnt:
            clave = (int(f.espacio_id), int(f.mes), int(f.dia))
            slot = agrupado.setdefault(clave, {"conteo": 0, "orden_ids": []})
            slot["conteo"] += int(f.conteo or 0)
    except Exception:
        pass

    # Programaciones Completadas agrupadas
    try:
        filas_prg = (
            db.query(
                Espacio.id.label("espacio_id"),
                func.date_part("month", Programacion.fecha_programada).label("mes"),
                func.date_part("day", Programacion.fecha_programada).label("dia"),
                func.count(Programacion.id).label("conteo"),
            )
            .join(Equipo, Equipo.id == Programacion.equipo_id)
            .join(Espacio, Espacio.id == Equipo.espacio_id)
            .filter(
                Programacion.estado == EstadoProgramacionEnum.COMPLETADO.value,
                func.date_part("year", Programacion.fecha_programada) == anio,
            )
            .group_by(
                Espacio.id,
                func.date_part("month", Programacion.fecha_programada),
                func.date_part("day", Programacion.fecha_programada),
            )
            .all()
        )
        for f in filas_prg:
            clave = (int(f.espacio_id), int(f.mes), int(f.dia))
            slot = agrupado.setdefault(clave, {"conteo": 0, "orden_ids": []})
            slot["conteo"] += int(f.conteo or 0)
    except Exception:
        pass

    return agrupado


def obtener_resumen_anual(db: Session, anio: int, limite: int = 5000) -> dict:
    """Construye el payload agregado del año."""
    # 1. Espacios canónicos
    espacios_db = (
        db.query(Espacio)
        .options(joinedload(Espacio.bloque))
        .order_by(Espacio.nombre.asc())
        .limit(2000)
        .all()
    )
    espacios_map: Dict[int, dict] = {}
    for e in espacios_db:
        bloque = getattr(e, "bloque", None)
        espacios_map[int(e.id)] = {
            "id": int(e.id),
            "nombre": str(getattr(e, "nombre", f"Espacio {e.id}")),
            "codigo_espacio": getattr(e, "codigo_espacio", None),
            "bloque_nombre": getattr(bloque, "nombre_bloque", None) if bloque else None,
            "piso": getattr(e, "piso", None),
            "total": 0,
        }

    # 2. Mantenimientos del año (detalle)
    mants = (
        db.query(Mantenimiento)
        .options(
            joinedload(Mantenimiento.encargado),
            joinedload(Mantenimiento.tipo),
            joinedload(Mantenimiento.equipo).joinedload(Equipo.espacio),
            joinedload(Mantenimiento.componentes_usados).joinedload(
                ComponenteUsado.componente
            ),
        )
        .filter(func.date_part("year", Mantenimiento.fecha_mantenimiento) == anio)
        .order_by(Mantenimiento.fecha_mantenimiento.asc())
        .limit(limite)
        .all()
    )

    # 3. Programaciones Completadas del año (detalle)
    progs = (
        db.query(Programacion)
        .options(
            joinedload(Programacion.encargado),
            joinedload(Programacion.tipo_mantenimiento),
            joinedload(Programacion.equipo).joinedload(Equipo.espacio),
        )
        .filter(
            Programacion.estado == EstadoProgramacionEnum.COMPLETADO.value,
            func.date_part("year", Programacion.fecha_programada) == anio,
        )
        .order_by(Programacion.fecha_programada.asc())
        .limit(limite)
        .all()
    )

    eventos: List[dict] = []
    por_mes = [0] * 12
    totales_espacio: Dict[int, int] = defaultdict(int)
    ordenes_por_celda: Dict[Tuple[int, int, int], List[str]] = defaultdict(list)

    def _resolver_espacio(equipo) -> Tuple[int, str]:
        esp = getattr(equipo, "espacio", None) if equipo else None
        if esp is not None and getattr(esp, "id", None) is not None:
            eid = int(esp.id)
            nombre = str(getattr(esp, "nombre", f"Espacio {eid}"))
            if eid not in espacios_map:
                espacios_map[eid] = {
                    "id": eid,
                    "nombre": nombre,
                    "codigo_espacio": getattr(esp, "codigo_espacio", None),
                    "bloque_nombre": None,
                    "piso": getattr(esp, "piso", None),
                    "total": 0,
                }
            return eid, nombre
        return 0, "Sin ubicación"

    for m in mants or []:
        fecha = getattr(m, "fecha_mantenimiento", None)
        if not fecha:
            continue
        equipo = getattr(m, "equipo", None)
        eid, enombre = _resolver_espacio(equipo)
        insumos = []
        try:
            for cu in getattr(m, "componentes_usados", None) or []:
                comp = getattr(cu, "componente", None)
                cant = float(getattr(cu, "cantidad", 0) or 0)
                precio = float(getattr(cu, "precio_unitario", 0) or 0)
                insumos.append(
                    {
                        "nombre": getattr(comp, "nombre", "Insumo") or "Insumo",
                        "cantidad": cant,
                        "precio_unitario": precio,
                        "subtotal": round(cant * precio, 2),
                    }
                )
        except Exception:
            insumos = []
        costo = getattr(m, "costo_servicio", 0)
        try:
            costo_f = float(costo) if costo is not None else None
        except Exception:
            costo_f = None
        tipo = getattr(m, "tipo", None)
        orden_id = f"MNT-{getattr(m, 'id', '?')}"
        mes = int(fecha.month) if hasattr(fecha, "month") else int(str(fecha).split("-")[1])
        dia = int(fecha.day) if hasattr(fecha, "day") else int(str(fecha).split("-")[2])
        eventos.append(
            {
                "orden_id": orden_id,
                "fecha": fecha,
                "fecha_ejecucion": fecha,
                "equipo_id": getattr(m, "equipo_id", None),
                "espacio_id": eid if eid != 0 else None,
                "espacio_nombre": enombre,
                "tecnico_nombre": _nombre_tecnico(getattr(m, "encargado", None)),
                "observaciones": getattr(m, "detalle_mantenimiento", None),
                "insumos_gastados": insumos,
                "costo_total": costo_f,
                "estado": "Completado",
                "origen": "mantenimiento",
            }
        )
        if 1 <= mes <= 12:
            por_mes[mes - 1] += 1
        totales_espacio[eid] += 1
        ordenes_por_celda[(eid, mes, dia)].append(orden_id)

    for p in progs or []:
        fecha = getattr(p, "fecha_programada", None)
        if not fecha:
            continue
        equipo = getattr(p, "equipo", None)
        eid, enombre = _resolver_espacio(equipo)
        tipo = getattr(p, "tipo_mantenimiento", None)
        tipo_nombre = getattr(tipo, "nombre", "") if tipo else ""
        orden_id = f"ORD-{str(getattr(p, 'id', 0)).zfill(3)}"
        mes = int(fecha.month) if hasattr(fecha, "month") else int(str(fecha).split("-")[1])
        dia = int(fecha.day) if hasattr(fecha, "day") else int(str(fecha).split("-")[2])
        eventos.append(
            {
                "orden_id": orden_id,
                "fecha": fecha,
                "fecha_ejecucion": fecha,
                "equipo_id": getattr(p, "equipo_id", None),
                "espacio_id": eid if eid != 0 else None,
                "espacio_nombre": enombre,
                "tecnico_nombre": _nombre_tecnico(getattr(p, "encargado", None)),
                "observaciones": f"Orden {orden_id} · {tipo_nombre}".strip(),
                "insumos_gastados": [],
                "costo_total": None,
                "estado": "Completado",
                "origen": "programacion",
            }
        )
        if 1 <= mes <= 12:
            por_mes[mes - 1] += 1
        totales_espacio[eid] += 1
        ordenes_por_celda[(eid, mes, dia)].append(orden_id)

    # 4. GROUP BY real como fuente de conteos (valida lo anterior)
    agrupado = _celdas_groupby(db, anio)

    celdas: List[dict] = []
    claves = set(list(agrupado.keys()) + list(ordenes_por_celda.keys()))
    for (eid, mes, dia) in sorted(claves):
        conteo = int(agrupado.get((eid, mes, dia), {}).get("conteo", 0))
        if conteo <= 0:
            conteo = len(ordenes_por_celda.get((eid, mes, dia), []))
        if conteo <= 0:
            continue
        celdas.append(
            {
                "espacio_id": int(eid),
                "mes": int(mes),
                "dia": int(dia),
                "conteo": int(conteo),
                "orden_ids": list(ordenes_por_celda.get((eid, mes, dia), []))[:10],
            }
        )

    # Sintético Sin ubicación si hizo falta
    if 0 in totales_espacio and 0 not in espacios_map:
        espacios_map[0] = {
            "id": 0,
            "nombre": "Sin ubicación",
            "codigo_espacio": None,
            "bloque_nombre": None,
            "piso": None,
            "total": 0,
        }

    espacios_out = []
    for eid in sorted(espacios_map.keys(), key=lambda k: (k == 0, str(espacios_map[k]["nombre"]).lower())):
        item = dict(espacios_map[eid])
        item["total"] = int(totales_espacio.get(eid, 0))
        espacios_out.append(item)

    eventos.sort(key=lambda e: str(e.get("fecha")))

    return {
        "anio": int(anio),
        "total_espacios": len(espacios_out),
        "total_eventos": len(eventos),
        "espacios": espacios_out,
        "celdas": celdas,
        "eventos": eventos,
        "por_mes": por_mes,
    }
