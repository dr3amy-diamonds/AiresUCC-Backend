from fastapi import APIRouter
from app.api.v1.endpoints import usuarios, auth, equipos, mantenimientos, programaciones, dashboard

api_router = APIRouter()

# Incluir routers de endpoints
api_router.include_router(auth.router)
api_router.include_router(usuarios.router)
api_router.include_router(equipos.router)
api_router.include_router(mantenimientos.router)
api_router.include_router(programaciones.router)
api_router.include_router(dashboard.router)
