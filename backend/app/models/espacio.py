"""
Modelo para la tabla de Espacios.
Representa las ubicaciones físicas (bloques y salones) de la UCC Montería.
"""

from typing import Optional
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class Espacio(Base):
    """
    Modelo SQLAlchemy para la tabla 'espacios'.

    Atributos:
        id (int): Identificador único del espacio.
        codigo_espacio (str): Identificador físico único en la puerta del salón.
        nombre (str): Nombre o número del salón/oficina (ej: 'Aula 204', 'Laboratorio 1').
        piso (int): Número de piso - ayuda a visualizar la distribución vertical en mapas o dashboards.
        bloque_id (int): FK a la tabla bloques.
        tipo_espacio_id (int): FK a la tabla tipos_espacios.

    Relaciones:
        bloque: Muchos a uno - Un espacio pertenece a un bloque
        equipos: Uno a muchos - Un espacio contiene múltiples equipos
    """

    __tablename__ = "espacios"

    id: int = Column(Integer, primary_key=True, index=True)
    codigo_espacio: str = Column(String(20), nullable=False, unique=True, index=True)
    nombre: str = Column(String(65), nullable=False, index=True)
    piso: Optional[int] = Column(Integer, nullable=True)

    # Claves foráneas
    bloque_id: int = Column(Integer, ForeignKey("gestion_aires_ucc.bloques.id"), nullable=False, index=True)
    tipo_espacio_id: int = Column(Integer, ForeignKey("gestion_aires_ucc.tipos_espacios.id"), nullable=False, index=True)

    # Relaciones
    bloque = relationship("Bloque", back_populates="espacios")
    tipo_espacio = relationship("TipoEspacio", foreign_keys=[tipo_espacio_id])
    equipos = relationship("Equipo", back_populates="espacio", overlaps="equipos_espacio")

    # Esquema de base de datos
    __table_args__ = {"schema": "gestion_aires_ucc"}
