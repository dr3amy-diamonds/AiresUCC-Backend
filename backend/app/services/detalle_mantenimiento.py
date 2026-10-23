"""
Parser de detalle_mantenimiento para historial de intervenciones.

El detalle se guarda como texto con 4 bloques:
  TRABAJO REALIZADO / HALLAZGOS TÉCNICOS / RECOMENDACIONES / ESTADO FINAL DEL EQUIPO

Catálogo único (2026-10-03):
  Operativo / En reparacion / Dado de baja

Mapeo de valores viejos:
  En Observación -> En reparacion
  Fuera de Servicio -> Dado de baja
  Inactivo -> Dado de baja
"""

import re
import unicodedata
from typing import Dict, Optional

ESTADOS_VALIDOS = ("Operativo", "En reparacion", "Dado de baja")

_ETIQUETAS = (
    "TRABAJO REALIZADO",
    "HALLAZGOS TÉCNICOS",
    "RECOMENDACIONES",
    "ESTADO FINAL DEL EQUIPO",
)


def _sin_tildes(texto: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn"
    )


def extraer_bloque(detalle: Optional[str], etiqueta: str) -> Optional[str]:
    """Extrae el contenido de un bloque por etiqueta, insensible a mayúsculas/tildes."""
    if not detalle:
        return None
    raw = detalle.strip()
    if not raw:
        return None
    # Construye regex que tolera variaciones de tildes/espacios
    # Simplificamos: normalizamos tanto patrón como texto para buscar.
    patron = re.compile(
        re.escape(etiqueta) + r"\s*:?\s*([\s\S]*?)(?=(TRABAJO REALIZADO|HALLAZGOS TÉCNICOS|HALLAZGOS TECNICOS|RECOMENDACIONES|ESTADO FINAL DEL EQUIPO)\s*:?\s*|$)",
        re.IGNORECASE,
    )
    for m in patron.finditer(raw):
        # Verificamos que el match corresponda a la etiqueta pedida (sin tildes)
        # El primer grupo alternativo puede haber capturado otra etiqueta; filtramos por posición:
        # Re-busca solo la etiqueta exacta al inicio del match.
        inicio = m.group(0)
        if _sin_tildes(etiqueta).lower() in _sin_tildes(inicio[: len(etiqueta) + 5]).lower():
            contenido = (m.group(1) or "").strip()
            return contenido or None
    return None


def normalizar_estado_final(raw: Optional[str]) -> Optional[str]:
    """Normaliza texto libre al catálogo de 3 estados. None si no reconoce."""
    if not raw:
        return None
    t = _sin_tildes(raw.strip().lower())
    if not t or t in ("—", "-", "ninguno", "ninguna", "n/a", "na"):
        # Ojo: "Ninguno" como estado no es válido -> None para pintar "—"
        # Pero si el bloque existe con "Operativo", sí matchea abajo primero.
        pass
    if "operativo" in t:
        return "Operativo"
    if "reparaci" in t or "observaci" in t:
        return "En reparacion"
    if "baja" in t or "fuera" in t or "inactivo" in t:
        return "Dado de baja"
    return None


def parse_detalle_mantenimiento(detalle: Optional[str]) -> Dict[str, Optional[str]]:
    """Devuelve dict con trabajo_realizado, hallazgos, recomendaciones, estado_final."""
    if not detalle or not str(detalle).strip():
        return {
            "trabajo_realizado": None,
            "hallazgos": None,
            "recomendaciones": None,
            "estado_final": None,
        }
    texto = str(detalle)
    trabajo = extraer_bloque(texto, "TRABAJO REALIZADO")
    hallazgos = extraer_bloque(texto, "HALLAZGOS TÉCNICOS")
    if hallazgos is None:
        hallazgos = extraer_bloque(texto, "HALLAZGOS TECNICOS")
    recomendaciones = extraer_bloque(texto, "RECOMENDACIONES")
    estado_raw = extraer_bloque(texto, "ESTADO FINAL DEL EQUIPO")
    estado = normalizar_estado_final(estado_raw)
    # Si no hay estructura de etiquetas, todo el texto es trabajo realizado.
    tiene_estructura = any(
        _sin_tildes(e).lower() in _sin_tildes(texto).lower() for e in _ETIQUETAS
    )
    if not tiene_estructura:
        trabajo = texto.strip()
    return {
        "trabajo_realizado": trabajo,
        "hallazgos": hallazgos,
        "recomendaciones": recomendaciones,
        "estado_final": estado,
    }
