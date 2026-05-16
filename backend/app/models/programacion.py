"""
Modelo para Programaciones de Mantenimiento.
Agenda de mantenimiento futuro. La API consultará esta tabla a diario para lanzar alertas.

Tabla física en PostgreSQL: gestion_aires_ucc.programaciones
Columnas: id, fecha_programada, equipo_id, encargado_id, tipo_mantenimiento_id, estado, mantenimiento_id
"""

from sqlalchemy import Column, Integer, Date, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class Programacion(Base):
    """
    Modelo SQLAlchemy para la tabla 'programaciones'.
    Cronograma de mantenimientos futuros.

    IMPORTANTE: Este modelo mapea EXACTAMENTE las columnas que existen en PostgreSQL.
    NO incluye observaciones ni created_at (columnas que no existen en la BD).

    Atributos:
        id (int): Identificador único (clave primaria).
        fecha_programada (date): Deadline de ejecución (YYYY-MM-DD).
        estado (str): Estado actual ('Pendiente', 'Completado', 'Cancelado', 'Vencido').
        equipo_id (int): FK a gestion_aires_ucc.equipos(id) - aire a mantener.
        encargado_id (int): FK a gestion_aires_ucc.encargados(id) - técnico responsable.
        tipo_mantenimiento_id (int): FK a gestion_aires_ucc.tipos_mantenimiento(id) - tipo de trabajo.
        mantenimiento_id (int, nullable): FK a gestion_aires_ucc.mantenimientos(id) - cuando se completa, enlaza al reporte real.
    """

    __tablename__ = "programaciones"
    __table_args__ = {"schema": "gestion_aires_ucc"}

    # Columnas simples
    id: int = Column(Integer, primary_key=True, index=True)
    fecha_programada: object = Column(Date, nullable=False, index=True)
    estado: str = Column(String(20), default="Pendiente", nullable=False, index=True)

    # Claves foráneas
    equipo_id: int = Column(Integer, ForeignKey("gestion_aires_ucc.equipos.id"), nullable=False, index=True)
    encargado_id: int = Column(Integer, ForeignKey("gestion_aires_ucc.encargados.id"), nullable=False, index=True)
    tipo_mantenimiento_id: int = Column(Integer, ForeignKey("gestion_aires_ucc.tipos_mantenimiento.id"), nullable=False, index=True)
    mantenimiento_id: int = Column(Integer, ForeignKey("gestion_aires_ucc.mantenimientos.id"), nullable=True, index=True)

    # Relaciones con otros modelos
    equipo = relationship("Equipo", backref="programaciones")
    encargado = relationship("Usuario", backref="programaciones")
    tipo_mantenimiento = relationship("TipoMantenimiento", backref="programaciones")
    mantenimiento = relationship("Mantenimiento", backref="programacion")


