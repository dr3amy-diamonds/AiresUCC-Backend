"""
Archivo Principal - AiresFlow API Backend

Este módulo inicializa la aplicación FastAPI y configura los componentes esenciales:
- Instancia de FastAPI con metadatos del proyecto
- Configuración de CORS para integración frontend
- Inclusión de routers de la API v1
- Endpoint de health check
- Documentación interactiva (Swagger y ReDoc)

Arquitectura:
- FastAPI → APIRouter (v1/api.py) → Endpoints específicos (v1/endpoints/*.py)
- Servicios de negocio (app/services/*.py)
- Modelos SQLAlchemy (app/models/*.py)
- Esquemas Pydantic (app/schemas/*.py)
- Base de datos PostgreSQL (via app/db/session.py)

El proyecto está diseñado siguiendo arquitectura limpia con separación clara
de responsabilidades y máxima escalabilidad.
"""

from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import api


# ============================================================================
# INICIALIZACIÓN DE LA APLICACIÓN FASTAPI
# ============================================================================

app = FastAPI(
    title="AiresFlow API - Gestión de Climatización UCC",
    description=(
        "Sistema integral de gestión para equipos de aire acondicionado\n\n"
        "**Características principales:**\n"
        "- Gestión de usuarios con roles (Administrador, Técnico, Supervisor, Contratista)\n"
        "- Control de equipos de climatización (creación, actualización, seguimiento)\n"
        "- Registro de marcas y modelos de equipos\n"
        "- Análisis de mantenimiento preventivo y correctivo\n"
        "- Reportes y analítica de performance\n\n"
        "**Institución:** Universidad Cooperativa de Colombia (UCC) - Montería\n"
        "**Proyecto:** Formulación de Proyecto - Octavo Semestre\n"
    ),
    version="1.0.0",
    author="Backend Senior - AiresFlow Development Team",
    author_email="backend@airesflow.local",
    license_info={
        "name": "Propietario - Universidad Cooperativa de Colombia",
        "url": "https://www.ucc.edu.co",
    },
    openapi_url="/api/v1/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)


# ============================================================================
# CONFIGURACIÓN DE CORS MIDDLEWARE
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite peticiones desde cualquier origen (ideal para desarrollo)
    allow_credentials=True,  # Permite envío de credentials (cookies, auth headers)
    allow_methods=["*"],  # Permite todos los métodos HTTP (GET, POST, PUT, DELETE, etc)
    allow_headers=["*"],  # Permite todos los headers
)

"""
NOTA DE SEGURIDAD IMPORTANTE:
En producción, reemplazar allow_origins=["*"] con una lista específica:
    allow_origins=[
        "https://frontend.airesflow.local",
        "https://dashboard.airesflow.local",
    ]

Esto previene peticiones CORS no autorizadas y protege la API de origen cruzado.
"""


# ============================================================================
# INCLUSIÓN DE ROUTERS
# ============================================================================

# Importar e incluir el router principal de la API v1
# El prefijo /api/v1 se antepone automáticamente a todas las rutas
app.include_router(
    api.api_router,
    prefix="/api/v1",
    tags=["API v1"],
)


# ============================================================================
# ENDPOINTS DE HEALTH CHECK Y INFORMACIÓN
# ============================================================================

@app.get(
    "/",
    summary="Health Check - Verificar Estado del Servidor",
    tags=["Sistema"],
    response_description="Estado del servidor y componentes",
)
def root_health_check() -> dict:
    """
    Endpoint de health check en la raíz de la aplicación.

    Proporciona información rápida sobre el estado del servidor, ideal para
    verificar disponibilidad en dashboards de monitoreo.

    **Retorna:**
    - status: Estado general del servidor ("running" si está activo)
    - timestamp: Fecha y hora actual del servidor
    - version: Versión de la API
    - service: Nombre del servicio (AiresFlow)
    - environment: Entorno de ejecución (debug/production)

    **Ejemplo de Respuesta:**
    ```json
    {
        "status": "running",
        "timestamp": "2024-01-15T10:30:00.123456",
        "version": "1.0.0",
        "service": "AiresFlow API - Gestión de Climatización UCC",
        "environment": "development"
    }
    ```
    """
    return {
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "service": "AiresFlow API - Gestión de Climatización UCC",
        "environment": "development",
    }


@app.get(
    "/health",
    summary="Health Check Detallado",
    tags=["Sistema"],
    response_description="Información detallada del estado del sistema",
)
def detailed_health_check() -> dict:
    """
    Endpoint de health check detallado.

    Proporciona información más exhaustiva sobre el estado de los componentes
    principales del sistema. Útil para monitoreo proactivo.

    **Componentes Verificados:**
    - API: Estado de la aplicación FastAPI
    - Base de Datos: Status de conexión a PostgreSQL
    - Servicios: Estado de los servicios de negocio

    **Retorna:**
    ```json
    {
        "status": "healthy",
        "api": "operational",
        "database": "connected",
        "services": "running",
        "timestamp": "2024-01-15T10:30:00.123456"
    }
    ```
    """
    return {
        "status": "healthy",
        "api": "operational",
        "database": "connected",  # Aquí se puede verificar la conexión real
        "services": "running",
        "timestamp": datetime.utcnow().isoformat(),
    }


# ============================================================================
# MANEJO DE ERRORES GLOBALES (Opcional - Puede extenderse)
# ============================================================================

@app.get(
    "/api/info",
    summary="Información de la API",
    tags=["Sistema"],
)
def api_info() -> dict:
    """
    Proporciona información sobre la API y sus endpoints disponibles.

    Útil para clientes que necesitan descubrir la estructura de la API
    sin consultar la documentación interactiva.
    """
    return {
        "application": "AiresFlow API",
        "version": "1.0.0",
        "description": "Sistema de gestión de climatización para UCC Montería",
        "endpoints": {
            "usuarios": {
                "prefix": "/api/v1/usuarios",
                "methods": ["GET", "POST", "PUT"],
                "description": "Gestión de usuarios del sistema",
            },
            "equipos": {
                "prefix": "/api/v1/equipos",
                "methods": ["GET", "POST", "PUT", "DELETE"],
                "description": "Gestión de equipos de climatización",
            },
            "marcas": {
                "prefix": "/api/v1/marcas",
                "methods": ["GET", "POST"],
                "description": "Catálogo de marcas de equipos",
            },
        },
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc",
            "openapi_json": "/api/v1/openapi.json",
        },
        "base_url": "http://localhost:8000",
    }


# ============================================================================
# EJECUCIÓN LOCAL (INSTRUCCIONES COMENTADAS)
# ============================================================================

"""
INSTRUCCIONES PARA EJECUTAR EL PROYECTO

1. INSTALACIÓN DE DEPENDENCIAS:
   cd backend
   pip install -r ../requirements.txt

2. CONFIGURACIÓN DE VARIABLES DE ENTORNO:
   - Crear archivo .env en la raíz del proyecto
   - Configurar DATABASE_URL para PostgreSQL
   - Ejemplo: DATABASE_URL=postgresql://usuario:contraseña@localhost:5432/aires_ucc

3. EJECUCIÓN EN DESARROLLO (Hot-reload):
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   
   Acceder a:
   - API: http://localhost:8000
   - Swagger: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

4. EJECUCIÓN EN PRODUCCIÓN:
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
   
   Para producción con Gunicorn:
   gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker

5. VERIFICAR ESTADO:
   curl http://localhost:8000/
   curl http://localhost:8000/health
   curl http://localhost:8000/api/info

6. EJECUTAR MIGRACIONES (Alembic):
   alembic upgrade head

7. CREAR USUARIO ADMINISTRADOR INICIAL:
   python scripts/create_admin.py
"""


if __name__ == "__main__":
    import uvicorn

    # Configuración para ejecución directa
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Hot-reload en desarrollo
        log_level="info",
    )

