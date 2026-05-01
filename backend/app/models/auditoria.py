"""
Modelo para Auditoría.
Historial a prueba de manipulaciones para saber quién cambió qué. La caja negra del sistema.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class Auditoria(Base):
    """
    Modelo SQLAlchemy para la tabla 'auditoria'.
    Registro inmutable de cambios en la base de datos.

    Atributos:
        id (int): Identificador único (clave primaria).
        tabla_afectada (str): Nombre de la tabla modificada.
        registro_id (int): ID del registro modificado.
        campo (str): Nombre del campo que cambió.
        valor_anterior (str): Valor antes del cambio.
        valor_nuevo (str): Valor después del cambio.
        fecha_cambio (datetime): Timestamp del cambio.
        encargado_id (int): FK a encargados - usuario autenticado que hizo el cambio.
    """

    __tablename__ = "auditoria"

    id: int = Column(Integer, primary_key=True, index=True)
    tabla_afectada: str = Column(String(60), nullable=False, index=True)
    registro_id: int = Column(Integer, nullable=False, index=True)
    campo: str = Column(String(60), nullable=False, index=True)
    valor_anterior: str = Column(Text, nullable=True)
    valor_nuevo: str = Column(Text, nullable=True)
    fecha_cambio: datetime = Column(DateTime, server_default="NOW()", nullable=False, index=True)

    # Claves foráneas
    encargado_id: int = Column(Integer, ForeignKey("gestion_aires_ucc.encargados.id"), nullable=True)

    # Relaciones
    encargado = relationship("Usuario", backref="auditorias")

    __table_args__ = {"schema": "gestion_aires_ucc"}

