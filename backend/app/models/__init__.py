"""
Módulo de modelos SQLAlchemy para el sistema de gestión de aires acondicionados.
Centraliza las importaciones de los modelos para facilitar su uso en toda la aplicación.
"""

from app.models.marca import Marca
from app.models.equipo import Equipo
from app.models.usuario import Usuario, TipoRol
from app.models.espacio import Espacio
from app.models.bloque import Bloque
from app.models.tipo_espacio import TipoEspacio
from app.models.tipo_equipo import TipoEquipo
from app.models.tipo_gas_refrigerante import TipoGasRefrigerante
from app.models.tipo_mantenimiento import TipoMantenimiento
from app.models.tipo_componente import TipoComponente
from app.models.mantenimiento import Mantenimiento
from app.models.componente_usado import ComponenteUsado
from app.models.programacion import Programacion
from app.models.auditoria import Auditoria

__all__ = [
    "Marca",
    "Equipo",
    "Usuario",
    "TipoRol",
    "Espacio",
    "Bloque",
    "TipoEspacio",
    "TipoEquipo",
    "TipoGasRefrigerante",
    "TipoMantenimiento",
    "TipoComponente",
    "Mantenimiento",
    "ComponenteUsado",
    "Programacion",
    "Auditoria",
]