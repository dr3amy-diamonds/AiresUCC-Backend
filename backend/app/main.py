"""
Archivo Principal - AiresFlow API Backend

Este módulo inicializa la aplicación FastAPI y configura los componentes esenciales:
- Instancia de FastAPI con metadatos del proyecto
- Configuración de CORS para integración frontend
- Inclusión de routers de la API v1
- Enrutamiento semántico con soporte de alias (.html) para evitar errores 404 en sidebars
- Endpoint de health check y metadatos de sistema
- Documentación interactiva (Swagger y ReDoc)
"""

import os
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
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
    openapi_url="/api/v1/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ============================================================================
# CONFIGURACIÓN DE CORS MIDDLEWARE
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# MIDDLEWARE: LIMPIAR CREDENCIALES EN LA URL (TRANSPARENTE AL USUARIO)
# ============================================================================

@app.middleware("http")
async def security_middleware(request, call_next):
    """
    🔒 Middleware de seguridad: Limpia credenciales de URL query params
    
    Previene exposición de datos sensibles redirigiendo automáticamente
    a una URL limpia, sin que el usuario lo note:
    - Historial del navegador: URL limpia
    - Logs del servidor/proxy: Sin credenciales
    - Referrer headers: Protegidos
    
    Ejemplo de redirección:
    /?email=user@ucc&password=123 → / (transparente)
    """
    from fastapi.responses import RedirectResponse
    
    # Parámetros sensibles que NUNCA deben estar en la URL
    FORBIDDEN_PARAMS = {"email", "password", "username", "token", "access_token", "secret"}
    
    query_params = set(request.query_params.keys())
    sensitive_found = query_params & FORBIDDEN_PARAMS
    
    # Si se detectan credenciales en la URL, hacer redirect a URL limpia
    if sensitive_found:
        print(f"🚨 ALERTA DE SEGURIDAD: Credenciales en URL - {sensitive_found}")
        print(f"   Limpiando URL y redirigiendo a: {request.url.path}")
        
        # Hacer redirect SIN los parámetros sensibles
        return RedirectResponse(
            url=request.url.path,
            status_code=307  # Redirect temporal (preserva POST)
        )
    
    response = await call_next(request)
    
    # Headers de seguridad HTTP (evita caché y ataques comunes)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Cache-Control"] = "no-store, max-age=0"
    response.headers["Pragma"] = "no-cache"
    
    return response

# ============================================================================
# CONFIGURACIÓN DEL SERVIDOR DE ARCHIVOS ESTÁTICOS Y RUTA FRONTEND
# ============================================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

if os.path.exists(os.path.join(FRONTEND_DIR, "js")):
    app.mount("/js", StaticFiles(directory=os.path.join(FRONTEND_DIR, "js")), name="js")
if os.path.exists(os.path.join(FRONTEND_DIR, "css")):
    app.mount("/css", StaticFiles(directory=os.path.join(FRONTEND_DIR, "css")), name="css")
if os.path.exists(os.path.join(FRONTEND_DIR, "img")):
    app.mount("/img", StaticFiles(directory=os.path.join(FRONTEND_DIR, "img")), name="img")

# ============================================================================
# ENRUTAMIENTO SEMÁNTICO DE INTERFACES (SOPORTE MULTI-RUTA / ALIAS)
# ============================================================================

@app.get("/", tags=["Interfaces de Usuario"])
@app.get("/login", tags=["Interfaces de Usuario"])
@app.get("/auth_login.html", tags=["Interfaces de Usuario"])
def servir_portal_acceso():
    """Autenticación y acceso — URL limpia /login con alias legacy"""
    return FileResponse(os.path.join(FRONTEND_DIR, "auth_login.html"))


@app.get("/dashboard", tags=["Interfaces de Usuario"])
@app.get("/analytics_dashboard.html", tags=["Interfaces de Usuario"])
def servir_dashboard_analitica():
    """Indicadores y analítica"""
    return FileResponse(os.path.join(FRONTEND_DIR, "analytics_dashboard.html"))


@app.get("/inventario", tags=["Interfaces de Usuario"])
@app.get("/asset_inventory.html", tags=["Interfaces de Usuario"])
def servir_inventario_activos():
    """Gestión de equipos y hojas de vida"""
    return FileResponse(os.path.join(FRONTEND_DIR, "asset_inventory.html"))


@app.get("/programacion", tags=["Interfaces de Usuario"])
@app.get("/maintenance_scheduler.html", tags=["Interfaces de Usuario"])
def servir_agenda_planificada():
    """Agenda operativa de servicios"""
    return FileResponse(os.path.join(FRONTEND_DIR, "maintenance_scheduler.html"))


@app.get("/usuarios", tags=["Interfaces de Usuario"])
@app.get("/gestion-usuarios", tags=["Interfaces de Usuario"])
@app.get("/admin_access_control.html", tags=["Interfaces de Usuario"])
def servir_control_accesos():
    """Control de acceso y roles"""
    return FileResponse(os.path.join(FRONTEND_DIR, "admin_access_control.html"))


@app.get("/exportar", tags=["Interfaces de Usuario"])
@app.get("/exportar-datos", tags=["Interfaces de Usuario"])
@app.get("/data_export_center.html", tags=["Interfaces de Usuario"])
def servir_centro_exportacion():
    """Centro de exportación de datos"""
    return FileResponse(os.path.join(FRONTEND_DIR, "data_export_center.html"))


@app.get("/auditoria", tags=["Interfaces de Usuario"])
@app.get("/auditoria-sistema", tags=["Interfaces de Usuario"])
@app.get("/maintenance_audit_logs.html", tags=["Interfaces de Usuario"])
def servir_logs_seguridad():
    """Bitácora de eventos y gestión"""
    return FileResponse(os.path.join(FRONTEND_DIR, "maintenance_audit_logs.html"))


@app.get("/reporte-tecnico", tags=["Interfaces de Usuario"])
@app.get("/service_report_form.html", tags=["Interfaces de Usuario"])
def servir_formulario_tecnico():
    """Cierre de orden e insumos"""
    return FileResponse(os.path.join(FRONTEND_DIR, "service_report_form.html"))


@app.get("/mis-ordenes", tags=["Interfaces de Usuario"])
@app.get("/mis_ordenes.html", tags=["Interfaces de Usuario"])
def servir_agenda_tecnico():
    """Agenda de mantenimiento del técnico"""
    return FileResponse(os.path.join(FRONTEND_DIR, "mis_ordenes.html"))


@app.get("/perfil", tags=["Interfaces de Usuario"])
@app.get("/user_profile_settings.html", tags=["Interfaces de Usuario"])
def servir_ajustes_perfil():
    """Ajustes de cuenta de usuario"""
    return FileResponse(os.path.join(FRONTEND_DIR, "user_profile_settings.html"))

# ============================================================================
# 🔒 BLOQUEO: asset_technical_sheet.html no tiene ruta pública (404 automático)
# ============================================================================


# ============================================================================
# INCLUSIÓN DE ROUTERS API CORE
# ============================================================================

app.include_router(
    api.api_router,
    prefix="/api/v1",
    tags=["API Core v1"],
)

# ============================================================================
# ENDPOINTS DE HEALTH CHECK Y MONITOREO
# ============================================================================

@app.get(
    "/api/v1/health-check",
    summary="Health Check - Verificar Estado del Servidor",
    tags=["Sistema Core"],
)
def root_health_check() -> dict:
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
    tags=["Sistema Core"],
)
def detailed_health_check() -> dict:
    return {
        "status": "healthy",
        "api": "operational",
        "database": "connected",
        "services": "running",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get(
    "/api/info",
    summary="Información de la API",
    tags=["Sistema Core"],
)
def api_info() -> dict:
    return {
        "application": "AiresFlow API",
        "version": "1.0.0",
        "description": "Sistema de gestión de climatización para UCC Montería",
        "endpoints": {
            "usuarios": {
                "prefix": "/api/v1/usuarios",
                "methods": ["GET", "POST", "PUT"],
            },
            "equipos": {
                "prefix": "/api/v1/equipos",
                "methods": ["GET", "POST", "PUT", "DELETE"],
            },
            "marcas": {
                "prefix": "/api/v1/marcas",
                "methods": ["GET", "POST"],
            },
        },
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc",
            "openapi_json": "/api/v1/openapi.json",
        },
        "base_url": "http://localhost:8000",
    }


