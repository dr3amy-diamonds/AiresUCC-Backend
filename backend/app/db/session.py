"""Gestión de sesiones PostgreSQL para FastAPI con SQLAlchemy 2.0."""

from typing import Generator
import os
from sqlalchemy import create_engine, pool, event
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
dotenv_path = os.path.join(os.path.dirname(__file__), '../../../.env')
load_dotenv(dotenv_path)

DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "postgresql://aires_user:password@localhost:5432/aires_ucc"
)

# Crear engine con pool de conexiones reusables para FastAPI
engine = create_engine(
    DATABASE_URL,
    echo=False,
    poolclass=pool.QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,      # Verifica conexión antes de usarla (evita stale connections)
    pool_recycle=3600,       # Recicla conexiones cada hora (PostgreSQL timeout)
)

# Event listeners para debugging (descomenta si necesitas ver logs de conexión)
@event.listens_for(engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    # print(f"Conexión abierta")
    pass

@event.listens_for(engine, "close")
def receive_close(dbapi_conn, connection_record):
    # print(f"Conexión cerrada ")
    pass

# Factory para crear sesiones con transacciones explícitas y mejor control
SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    autocommit=False,        # Transacciones explícitas (db.commit() obligatorio)
    autoflush=False,         # Flush manual para mejor rendimiento
    expire_on_commit=True,   # Refrescar objetos después de commit
)

def get_db() -> Generator[Session, None, None]:
    """
    Dependencia FastAPI que proporciona sesión de BD con limpieza garantizada.

    Uso: db: Session = Depends(get_db) en los endpoints.
    Garantiza rollback en excepciones y cierre de conexión en finally.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        print(f"Error en transacción: {str(e)}")
        raise
    finally:
        db.close()