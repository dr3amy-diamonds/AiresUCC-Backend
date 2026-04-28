from fastapi import APIRouter
from app.api.v1.endpoints import usuarios, auth

api_router = APIRouter()

# Incluir routers de endpoints
api_router.include_router(usuarios.router)
api_router.include_router(auth.router)
