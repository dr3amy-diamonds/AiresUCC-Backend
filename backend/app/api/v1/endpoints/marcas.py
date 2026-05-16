"""
Endpoints para la entidad Marca.
API REST para la gestión del catálogo de fabricantes de equipos de aire acondicionado.

Características:
- Creación de marcas con validación de unicidad (case-insensitive)
- Listado de todas las marcas
- Obtención de detalles de una marca específica
- Actualización de datos de marcas
- Eliminación de marcas
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.models.marca import Marca
from app.schemas.marca import (
    MarcaCreate,
    MarcaUpdate,
    MarcaResponse
)

router = APIRouter(prefix="/marcas", tags=["marcas"])


# ============================================================================
# ENDPOINTS DE LECTURA (GET)
# ============================================================================

@router.get("/", response_model=List[MarcaResponse])
def listar_marcas(
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(100, ge=1, le=500, description="Límite de registros por página"),
    db: Session = Depends(get_db)
):
    """
    Lista todas las marcas registradas en el catálogo.

    **Parámetros de Query:**
    - skip (int): Registros a saltar (para paginación)
    - limit (int): Límite de registros por página (máximo 500)

    **Respuesta:**
    - Lista de marcas con ID y nombre

    **Ejemplo de uso:**
    - GET /marcas?skip=0&limit=50  → Primeras 50 marcas
    """
    marcas = db.query(Marca).offset(skip).limit(limit).all()
    return marcas


@router.get("/{marca_id}", response_model=MarcaResponse)
def obtener_marca(
    marca_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene los detalles de una marca específica por su ID.

    **Parámetros:**
    - marca_id (int): Identificador único de la marca

    **Respuesta (200):**
    - Datos completos de la marca

    **Errores:**
    - 404: La marca no existe

    **Ejemplo:**
    GET /marcas/1
    """
    marca = db.query(Marca).filter(Marca.id == marca_id).first()

    if not marca:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"La marca con ID {marca_id} no existe"
        )

    return marca


# ============================================================================
# ENDPOINTS DE CREACIÓN (POST)
# ============================================================================

@router.post("/", response_model=MarcaResponse, status_code=status.HTTP_201_CREATED)
def crear_marca(
    marca_in: MarcaCreate,
    db: Session = Depends(get_db)
):
    """
    Crea una nueva marca en el catálogo.

    **Validación de Unicidad:**
    ✓ Verifica que el nombre de marca NO exista (case-insensitive)
    ✓ Si existe "Samsung" y se intenta "samsung", rechaza (400 Bad Request)
    ✓ Nombres válidos: máximo 20 caracteres

    **Request Body:**
    ```json
    {
        "nombre": "Samsung"
    }
    ```

    **Respuesta (201 Created):**
    - Datos de la marca creada con ID asignado

    **Errores Posibles:**
    - 400: Nombre de marca ya existe (case-insensitive)
    - 422: Error en validación Pydantic

    **Ejemplo de Uso:**
    ```bash
    POST /marcas
    Content-Type: application/json

    {
        "nombre": "LG"
    }
    ```

    **Respuesta correcta (201):**
    ```json
    {
        "id": 1,
        "nombre": "LG"
    }
    ```

    **Error - nombre duplicado (case-insensitive):**
    ```json
    {
        "detail": "La marca 'LG' ya existe en el catálogo (búsqueda case-insensitive)"
    }
    ```
    """
    try:
        # 1. VALIDACIÓN DE INTEGRIDAD: Verificar que el nombre NO existe (case-insensitive)
        # Búsqueda case-insensitive usando LOWER()
        marca_existente = db.query(Marca).filter(
            func.lower(Marca.nombre) == func.lower(marca_in.nombre)
        ).first()

        if marca_existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"La marca '{marca_in.nombre}' ya existe en el catálogo (búsqueda case-insensitive). Especifique una marca única."
            )

        # 2. Crear la nueva marca
        datos_marca = marca_in.model_dump()
        nueva_marca = Marca(**datos_marca)

        # Agregar a la sesión y hacer commit
        db.add(nueva_marca)
        db.commit()
        db.refresh(nueva_marca)

        return nueva_marca

    except HTTPException:
        # Re-lanzar excepciones HTTP
        raise
    except Exception as e:
        db.rollback()
        # Manejar errores inesperados
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al crear marca: {str(e)}"
        )


# ============================================================================
# ENDPOINTS DE ACTUALIZACIÓN (PUT)
# ============================================================================

@router.put("/{marca_id}", response_model=MarcaResponse)
def actualizar_marca(
    marca_id: int,
    marca_in: MarcaUpdate,
    db: Session = Depends(get_db)
):
    """
    Actualiza el nombre de una marca existente.

    **Validaciones:**
    - El nuevo nombre no puede ser duplicado (case-insensitive)
    - Se puede cambiar el nombre de la marca

    **Parámetros:**
    - marca_id (int): ID de la marca a actualizar

    **Request Body:**
    ```json
    {
        "nombre": "Samsung Electronics"
    }
    ```

    **Respuesta (200):**
    - Datos de la marca actualizada

    **Errores:**
    - 404: La marca no existe
    - 400: Nombre duplicado (case-insensitive)

    **Ejemplo:**
    ```bash
    PUT /marcas/1
    {
        "nombre": "LG Electronics"
    }
    ```
    """
    marca = db.query(Marca).filter(Marca.id == marca_id).first()

    if not marca:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"La marca con ID {marca_id} no existe"
        )

    try:
        # Si se intenta actualizar el nombre, validar que no exista otro con ese nombre
        if marca_in.nombre and marca_in.nombre != marca.nombre:
            marca_nombre_existe = db.query(Marca).filter(
                func.lower(Marca.nombre) == func.lower(marca_in.nombre),
                Marca.id != marca_id
            ).first()

            if marca_nombre_existe:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"La marca '{marca_in.nombre}' ya existe. Especifique un nombre único."
                )

        # Actualizar solo los campos permitidos
        datos_update = marca_in.model_dump(exclude_unset=True)
        for campo, valor in datos_update.items():
            if valor is not None:
                setattr(marca, campo, valor)

        db.commit()
        db.refresh(marca)
        return marca

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al actualizar marca: {str(e)}"
        )


# ============================================================================
# ENDPOINTS DE ELIMINACIÓN (DELETE)
# ============================================================================

@router.delete("/{marca_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_marca(
    marca_id: int,
    db: Session = Depends(get_db)
):
    """
    Elimina una marca del catálogo.

    **IMPORTANTE:** Esta operación puede ser irreversible. Si existen equipos
    asociados a la marca, la operación fallará por restricción de integridad.

    **Parámetros:**
    - marca_id (int): ID de la marca a eliminar

    **Respuesta (204):** Sin contenido (eliminación exitosa)

    **Errores:**
    - 404: La marca no existe
    - 409: Conflict - Existen equipos asociados a la marca

    **Ejemplo:**
    DELETE /marcas/1
    """
    marca = db.query(Marca).filter(Marca.id == marca_id).first()

    if not marca:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"La marca con ID {marca_id} no existe"
        )

    try:
        db.delete(marca)
        db.commit()
    except Exception as e:
        db.rollback()
        if "foreign key" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No se puede eliminar la marca: existen equipos asociados"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al eliminar marca: {str(e)}"
        )

