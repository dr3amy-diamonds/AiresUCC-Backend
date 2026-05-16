"""
Endpoints para la entidad Bloque.
API REST para la gestión integral de bloques (edificios) de la institución.

Características:
- Creación de bloques con validación de unicidad en codigo_bloque y nombre_bloque
- Listado paginado de todos los bloques
- Obtención de detalles de un bloque específico
- Actualización de bloques (sin cambiar codigo_bloque por auditoría)
- Eliminación lógica o física de bloques
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.models.bloque import Bloque
from app.schemas.bloque import (
    BloqueCreate,
    BloqueUpdate,
    BloqueResponse,
    BloqueListResponse
)

router = APIRouter(prefix="/bloques", tags=["bloques"])


# ============================================================================
# ENDPOINTS DE LECTURA (GET)
# ============================================================================

@router.get("/", response_model=BloqueListResponse)
def listar_bloques(
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(10, ge=1, le=100, description="Límite de registros por página"),
    db: Session = Depends(get_db)
):
    """
    Lista todos los bloques registrados con paginación.

    **Parámetros de Query:**
    - skip (int): Registros a saltar (para paginación)
    - limit (int): Límite de registros por página (máximo 100)

    **Respuesta:**
    - total: Total de bloques en la base de datos
    - page: Número de página actual
    - size: Registros por página
    - items: Lista de bloques

    **Ejemplo de uso:**
    - GET /bloques?skip=0&limit=20          → Primeros 20 bloques
    - GET /bloques?skip=20&limit=10         → Bloques 21-30
    """
    total = db.query(func.count(Bloque.id)).scalar() or 0
    bloques = db.query(Bloque).offset(skip).limit(limit).all()

    return {
        "total": total,
        "page": (skip // limit) + 1,
        "size": limit,
        "items": bloques
    }


@router.get("/{bloque_id}", response_model=BloqueResponse)
def obtener_bloque(
    bloque_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene los detalles de un bloque específico por su ID.

    **Parámetros:**
    - bloque_id (int): Identificador único del bloque

    **Respuesta (200):**
    - Datos completos del bloque incluyendo id, codigo_bloque, nombre_bloque, descripcion

    **Errores:**
    - 404: El bloque no existe

    **Ejemplo:**
    GET /bloques/1
    """
    bloque = db.query(Bloque).filter(Bloque.id == bloque_id).first()

    if not bloque:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El bloque con ID {bloque_id} no existe"
        )

    return bloque


# ============================================================================
# ENDPOINTS DE CREACIÓN (POST)
# ============================================================================

@router.post("/", response_model=BloqueResponse, status_code=status.HTTP_201_CREATED)
def crear_bloque(
    bloque_in: BloqueCreate,
    db: Session = Depends(get_db)
):
    """
    Crea un nuevo bloque en la base de datos.

    **Validación de Unicidad (500ms max):**
    ✓ Verifica que codigo_bloque NO exista (400 si existe)
    ✓ Verifica que nombre_bloque NO exista (400 si existe)
    ✓ Valida estructura y longitudes de campos (Pydantic)

    **Request Body:**
    ```json
    {
        "codigo_bloque": "BLOQUE-A",
        "nombre_bloque": "Bloque Academia"
    }
    ```

    **Respuesta (201 Created):**
    - Datos del bloque creado con ID asignado por la BD

    **Errores Posibles:**
    - 400: codigo_bloque ya existe
    - 400: nombre_bloque ya existe
    - 422: Error en validación Pydantic (campos inválidos)

    **Ejemplo de Uso:**
    ```bash
    POST /bloques
    Content-Type: application/json

    {
        "codigo_bloque": "BLOQUE-ADM",
        "nombre_bloque": "Bloque Administrativo"
    }
    ```

    **Respuesta correcta (201):**
    ```json
    {
        "id": 2,
        "codigo_bloque": "BLOQUE-ADM",
        "nombre_bloque": "Bloque Administrativo"
    }
    ```

    **Error - codigo_bloque duplicado:**
    ```json
    {
        "detail": "El codigo_bloque 'BLOQUE-A' ya existe. Especifique un código único."
    }
    ```

    **Error - nombre_bloque duplicado:**
    ```json
    {
        "detail": "El nombre_bloque 'Bloque Academia' ya existe. Especifique un nombre único."
    }
    ```
    """
    try:
        # 1. VALIDACIÓN DE INTEGRIDAD: Verificar que codigo_bloque no existe
        bloque_existente_codigo = db.query(Bloque).filter(
            Bloque.codigo_bloque == bloque_in.codigo_bloque
        ).first()

        if bloque_existente_codigo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El codigo_bloque '{bloque_in.codigo_bloque}' ya existe. Especifique un código único."
            )

        # 2. VALIDACIÓN DE INTEGRIDAD: Verificar que nombre_bloque no existe
        bloque_existente_nombre = db.query(Bloque).filter(
            Bloque.nombre_bloque == bloque_in.nombre_bloque
        ).first()

        if bloque_existente_nombre:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El nombre_bloque '{bloque_in.nombre_bloque}' ya existe. Especifique un nombre único."
            )

        # 3. Crear el nuevo bloque
        datos_bloque = bloque_in.model_dump()
        nuevo_bloque = Bloque(**datos_bloque)

        # Agregar a la sesión y hacer commit
        db.add(nuevo_bloque)
        db.commit()
        db.refresh(nuevo_bloque)

        return nuevo_bloque

    except HTTPException:
        # Re-lanzar excepciones HTTP (400, etc)
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        # Manejar errores inesperados
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al crear bloque: {str(e)}"
        )


# ============================================================================
# ENDPOINTS DE ACTUALIZACIÓN (PUT)
# ============================================================================

@router.put("/{bloque_id}", response_model=BloqueResponse)
def actualizar_bloque(
    bloque_id: int,
    bloque_in: BloqueUpdate,
    db: Session = Depends(get_db)
):
    """
    Actualiza los datos de un bloque existente.

    **Restricciones:**
    - NO se puede cambiar: codigo_bloque (auditoría)
    - Se puede cambiar: nombre_bloque
    - Para cambiar codigo_bloque, cree un nuevo bloque (auditoría)

    **Parámetros:**
    - bloque_id (int): ID del bloque a actualizar

    **Request Body (opcional):**
    ```json
    {
        "nombre_bloque": "Bloque Principal"
    }
    ```

    **Respuesta (200):**
    - Datos del bloque actualizado

    **Errores:**
    - 404: El bloque no existe
    - 400: nombre_bloque duplicado (si se intenta cambiar)
    - 422: Error en validación Pydantic

    **Ejemplo:**
    ```bash
    PUT /bloques/1
    Content-Type: application/json

    {
        "nombre_bloque": "Bloque Principal"
    }
    ```
    """
    bloque = db.query(Bloque).filter(Bloque.id == bloque_id).first()

    if not bloque:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El bloque con ID {bloque_id} no existe"
        )

    try:
        # Si se intenta actualizar nombre_bloque, validar que no exista otro con ese nombre
        if bloque_in.nombre_bloque and bloque_in.nombre_bloque != bloque.nombre_bloque:
            bloque_nombre_existe = db.query(Bloque).filter(
                Bloque.nombre_bloque == bloque_in.nombre_bloque,
                Bloque.id != bloque_id
            ).first()

            if bloque_nombre_existe:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El nombre_bloque '{bloque_in.nombre_bloque}' ya existe. Especifique un nombre único."
                )

        # Actualizar solo los campos permitidos
        datos_update = bloque_in.model_dump(exclude_unset=True)
        for campo, valor in datos_update.items():
            setattr(bloque, campo, valor)

        db.commit()
        db.refresh(bloque)
        return bloque

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al actualizar bloque: {str(e)}"
        )


# ============================================================================
# ENDPOINTS DE ELIMINACIÓN (DELETE)
# ============================================================================

@router.delete("/{bloque_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_bloque(
    bloque_id: int,
    db: Session = Depends(get_db)
):
    """
    Elimina un bloque (lógicamente - marca como inactivo o eliminación física).

    **IMPORTANTE:** Esta operación puede ser irreversible. Si existen espacios
    asociados al bloque, la operación fallará por restricción de integridad.

    **Parámetros:**
    - bloque_id (int): ID del bloque a eliminar

    **Respuesta (204):** Sin contenido (eliminación exitosa)

    **Errores:**
    - 404: El bloque no existe
    - 409: Conflict - Existen espacios asociados al bloque

    **Ejemplo:**
    DELETE /bloques/1
    """
    bloque = db.query(Bloque).filter(Bloque.id == bloque_id).first()

    if not bloque:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El bloque con ID {bloque_id} no existe"
        )

    try:
        db.delete(bloque)
        db.commit()
    except Exception as e:
        db.rollback()
        if "foreign key" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No se puede eliminar el bloque: existen espacios asociados"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al eliminar bloque: {str(e)}"
        )

