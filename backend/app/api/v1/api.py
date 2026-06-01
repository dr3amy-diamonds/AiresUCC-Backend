from fastapi import APIRouter
from app.api.v1.endpoints import usuarios, auth, equipos, mantenimientos, programaciones, dashboard, espacios, bloques, marcas, tipo_componentes, tipo_equipos

api_router = APIRouter()

# Incluir routers de endpoints
api_router.include_router(auth.router)
api_router.include_router(usuarios.router)
api_router.include_router(bloques.router)
api_router.include_router(equipos.router)
api_router.include_router(mantenimientos.router)
api_router.include_router(programaciones.router)
api_router.include_router(dashboard.router)
api_router.include_router(espacios.router)
api_router.include_router(marcas.router)
api_router.include_router(tipo_componentes.router)
api_router.include_router(tipo_equipos.router)
