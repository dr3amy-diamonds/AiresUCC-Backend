"""
Modelo para Programaciones de Mantenimiento.
Agenda de mantenimiento futuro. La API consultará esta tabla a diario para lanzar alertas.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, Date, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class Programacion(Base):
    """
    Modelo SQLAlchemy para la tabla 'programaciones'.
    Cronograma de mantenimientos futuros.

    Atributos:
        id (int): Identificador único (clave primaria).
        fecha_programada (date): Deadline de ejecución.
        estado (str): Estado actual ('Pendiente', 'Completado', 'Cancelado', 'Vencido').
        equipo_id (int): FK a equipos - aire a mantener.
        encargado_id (int): FK a encargados - técnico responsable.
        tipo_mantenimiento_id (int): FK a tipos_mantenimiento - tipo de trabajo.
        mantenimiento_id (int): FK a mantenimientos - cuando se completa, enlaza al reporte real.
        observaciones (str): Notas adicionales.
        created_at (datetime): Timestamp de creación.
    """

    __tablename__ = "programaciones"

    id: int = Column(Integer, primary_key=True, index=True)
    fecha_programada: datetime = Column(Date, nullable=False, index=True)
    estado: str = Column(String(20), default="Pendiente", nullable=False, index=True)
    observaciones: str = Column(String(500), nullable=True)
    created_at: datetime = Column(DateTime, server_default="NOW()", nullable=False)

    # Claves foráneas
    equipo_id: int = Column(Integer, ForeignKey("gestion_aires_ucc.equipos.id"), nullable=False, index=True)
    encargado_id: int = Column(Integer, ForeignKey("gestion_aires_ucc.encargados.id"), nullable=False, index=True)
    tipo_mantenimiento_id: int = Column(Integer, ForeignKey("gestion_aires_ucc.tipos_mantenimiento.id"), nullable=False, index=True)
    mantenimiento_id: int = Column(Integer, ForeignKey("gestion_aires_ucc.mantenimientos.id"), nullable=True)

    # Relaciones
    equipo = relationship("Equipo", backref="programaciones")
    encargado = relationship("Usuario", backref="programaciones")
    tipo_mantenimiento = relationship("TipoMantenimiento", backref="programaciones")
    mantenimiento = relationship("Mantenimiento", backref="programacion")

    __table_args__ = {"schema": "gestion_aires_ucc"}

