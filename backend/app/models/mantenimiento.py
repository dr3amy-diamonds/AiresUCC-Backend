"""
Modelo para Historial de Mantenimientos.
Bitácora inmutable de lo que ya sucedió. Fundamental para auditorías de calidad.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class Mantenimiento(Base):
    """
    Modelo SQLAlchemy para la tabla 'mantenimientos'.
    Registro histórico de trabajos de mantenimiento realizados.

    Atributos:
        id (int): Identificador único (clave primaria).
        fecha_mantenimiento (date): Fecha real de ejecución del mantenimiento.
        detalle_mantenimiento (str): Descripción del trabajo realizado.
        created_at (datetime): Timestamp de creación del registro.
        equipo_id (int): FK a equipos - aire que fue mantenido.
        encargado_id (int): FK a encargados - técnico que realizó el trabajo.
        tipo_mantenimiento_id (int): FK a tipos_mantenimiento - tipo de trabajo.
        registrado_por (int): FK a encargados - quién digitó el dato en el sistema.
    """

    __tablename__ = "mantenimientos"

    id: int = Column(Integer, primary_key=True, index=True)
    fecha_mantenimiento: datetime = Column(Date, nullable=False, index=True)
    detalle_mantenimiento: str = Column(Text, nullable=True)
    created_at: datetime = Column(DateTime, server_default=func.now(), nullable=False)

    # Claves foráneas
    equipo_id: int = Column(Integer, ForeignKey("gestion_aires_ucc.equipos.id"), nullable=False, index=True)
    encargado_id: int = Column(Integer, ForeignKey("gestion_aires_ucc.encargados.id"), nullable=False, index=True)
    tipo_mantenimiento_id: int = Column(Integer, ForeignKey("gestion_aires_ucc.tipos_mantenimiento.id"), nullable=False, index=True)
    registrado_por: int = Column(Integer, ForeignKey("gestion_aires_ucc.encargados.id"), nullable=False, index=True)

    # Relaciones
    equipo = relationship("Equipo", backref="mantenimientos")
    tecnico = relationship("Usuario", foreign_keys=[encargado_id], backref="mantenimientos_realizados")
    tipo_mantenimiento = relationship("TipoMantenimiento", backref="mantenimientos")
    registrador = relationship("Usuario", foreign_keys=[registrado_por], backref="mantenimientos_registrados")

    __table_args__ = {"schema": "gestion_aires_ucc"}

