from fastapi import APIRouter
from app.api.v1.endpoints import usuarios, auth, equipos, mantenimientos, programaciones, dashboard, espacios, bloques, marcas, tipo_componentes, tipo_equipos, tipos_espacios, tipos_gas_refrigerante, tipos_mantenimiento, auditoria

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
api_router.include_router(tipos_espacios.router)
api_router.include_router(tipos_gas_refrigerante.router)
api_router.include_router(tipos_mantenimiento.router)
api_router.include_router(auditoria.router)
