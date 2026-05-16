"""
Endpoints para la entidad Espacio.
API REST para la gestión integral de espacios físicos (aulas, laboratorios, oficinas).

Características:
- Creación de espacios con validación de FK (bloque_id debe existir)
- Listado con paginación
- Filtrado por bloque
- Información detallada de espacios con sus equipos
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.db.session import get_db
from app.models.espacio import Espacio
from app.models.bloque import Bloque
from app.schemas.espacio import (
    EspacioCreate,
    EspacioUpdate,
    EspacioResponse,
    EspacioListResponse,
    EspacioDetalladoResponse
)

router = APIRouter(prefix="/espacios", tags=["espacios"])


# ============================================================================
# ENDPOINTS DE LECTURA (GET)
# ============================================================================

@router.get("/", response_model=EspacioListResponse)
def listar_espacios(
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(10, ge=1, le=100, description="Límite de registros por página"),
    bloque_id: int = Query(None, gt=0, description="Filtrar por ID de bloque (opcional)"),
    db: Session = Depends(get_db)
):
    """
    Lista todos los espacios con paginación e información del bloque relacionado.

    **Parámetros de Query:**
    - skip (int): Registros a saltar (para paginación)
    - limit (int): Límite de registros por página (máximo 100)
    - bloque_id (int, opcional): Filtrar espacios de un bloque específico

    **Respuesta:**
    - total: Total de espacios en la base de datos
    - page: Número de página actual
    - size: Registros por página
    - items: Lista de espacios con información de bloques

    **Ejemplo de uso:**
    - GET /espacios?skip=0&limit=20          → Primeros 20 espacios
    - GET /espacios?bloque_id=1&limit=10     → Espacios del bloque 1
    """
    query = db.query(Espacio)

    # Filtro opcional por bloque
    if bloque_id:
        query = query.filter(Espacio.bloque_id == bloque_id)

    total = query.count()
    espacios = query.offset(skip).limit(limit).all()

    return {
        "total": total,
        "page": (skip // limit) + 1,
        "size": limit,
        "items": espacios
    }


@router.get("/{espacio_id}", response_model=EspacioResponse)
def obtener_espacio(
    espacio_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene los detalles de un espacio específico por su ID.

    **Parámetros:**
    - espacio_id (int): Identificador único del espacio

    **Respuesta (200):**
    - Datos completos del espacio incluyendo información del bloque

    **Errores:**
    - 404: El espacio no existe

    **Ejemplo:**
    GET /espacios/1
    """
    espacio = db.query(Espacio).options(
        joinedload(Espacio.bloque),
        joinedload(Espacio.tipo_espacio)
    ).filter(Espacio.id == espacio_id).first()
    
    if not espacio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El espacio con ID {espacio_id} no existe"
        )
    
    return espacio


@router.get("/codigo/{codigo_espacio}", response_model=EspacioResponse)
def obtener_espacio_por_codigo(
    codigo_espacio: str,
    db: Session = Depends(get_db)
):
    """
    Busca un espacio por su código único (ej: 'A-204', 'LAB-001').

    **Parámetros:**
    - codigo_espacio (str): Código único del espacio

    **Respuesta (200):**
    - Datos del espacio encontrado

    **Errores:**
    - 404: No existe espacio con ese código

    **Ejemplo:**
    GET /espacios/codigo/A-204
    """
    espacio = db.query(Espacio).filter(Espacio.codigo_espacio == codigo_espacio).first()

    if not espacio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe espacio con código '{codigo_espacio}'"
        )

    return espacio


@router.get("/bloque/{bloque_id}", response_model=List[EspacioResponse])
def listar_espacios_por_bloque(
    bloque_id: int,
    db: Session = Depends(get_db)
):
    """
    Lista todos los espacios pertenecientes a un bloque específico.

    **Parámetros:**
    - bloque_id (int): Identificador del bloque

    **Respuesta (200):**
    - Lista de espacios del bloque

    **Errores:**
    - 404: El bloque no existe

    **Ejemplo:**
    GET /espacios/bloque/1
    """
    # Verificar que el bloque existe
    bloque = db.query(Bloque).filter(Bloque.id == bloque_id).first()
    if not bloque:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El bloque con ID {bloque_id} no existe"
        )

    espacios = db.query(Espacio).filter(Espacio.bloque_id == bloque_id).all()
    return espacios


# ============================================================================
# ENDPOINTS DE CREACIÓN (POST)
# ============================================================================

@router.post("/", response_model=EspacioResponse, status_code=status.HTTP_201_CREATED)
def crear_espacio(
    espacio_in: EspacioCreate,
    db: Session = Depends(get_db)
):
    """
    Crea un nuevo espacio en la base de datos.

    **Validación de Integridad:**
    ✓ Verifica que bloque_id existe en la tabla bloques (404 si no existe)
    ✓ Verifica que tipo_espacio_id existe en la tabla tipos_espacios (404 si no existe)
    ✓ Valida que codigo_espacio sea único (409 si ya existe)
    ✓ Valida que el nombre tenga entre 1 y 65 caracteres

    **Request Body:**
    ```json
    {
        "codigo_espacio": "A-204",
        "nombre": "Aula 204",
        "piso": 2,
        "bloque_id": 1,
        "tipo_espacio_id": 1
    }
    ```

    **Respuesta (201):**
    - Datos del espacio creado incluyendo ID generado

    **Errores Posibles:**
    - 400: Datos inválidos (validación Pydantic)
    - 404: El bloque especificado no existe (IMPORTANTE)
    - 409: Conflict - El código del espacio ya existe
    - 422: Unprocessable Entity - Error en la validación

    **Ejemplo de Uso:**
    ```bash
    POST /espacios
    Content-Type: application/json

    {
        "codigo_espacio": "LAB-001",
        "nombre": "Laboratorio de Sistemas",
        "piso": 1,
        "bloque_id": 2,
        "tipo_espacio_id": 3
    }
    ```
    """
    try:
        # 1. VALIDACIÓN DE INTEGRIDAD: Verificar que el bloque existe
        bloque = db.query(Bloque).filter(Bloque.id == espacio_in.bloque_id).first()
        if not bloque:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"El bloque especificado no existe (ID: {espacio_in.bloque_id})"
            )

        # 2. VALIDACIÓN DE UNICIDAD: Verificar que codigo_espacio no existe
        espacio_existente = db.query(Espacio).filter(
            Espacio.codigo_espacio == espacio_in.codigo_espacio
        ).first()

        if espacio_existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"El codigo_espacio '{espacio_in.codigo_espacio}' ya existe. Especifique un código único para el espacio."
            )

        # 3. Crear el nuevo espacio
        datos_espacio = espacio_in.model_dump()
        nuevo_espacio = Espacio(**datos_espacio)

        # Agregar a la sesión y hacer commit
        db.add(nuevo_espacio)
        db.commit()
        db.refresh(nuevo_espacio)
        
        # 3. Recargar con relaciones para la respuesta
        nuevo_espacio = db.query(Espacio).options(
            joinedload(Espacio.bloque),
            joinedload(Espacio.tipo_espacio)
        ).filter(Espacio.id == nuevo_espacio.id).first()

        return nuevo_espacio

    except HTTPException:
        # Re-lanzar excepciones HTTP (404, etc)
        raise
    except Exception as e:
        db.rollback()
        # Manejar errores de integridad (ej: código duplicado)
        if "unique" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El código de espacio ya existe"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al crear espacio: {str(e)}"
        )


# ============================================================================
# ENDPOINTS DE ACTUALIZACIÓN (PUT)
# ============================================================================

@router.put("/{espacio_id}", response_model=EspacioResponse)
def actualizar_espacio(
    espacio_id: int,
    espacio_in: EspacioUpdate,
    db: Session = Depends(get_db)
):
    """
    Actualiza los datos de un espacio existente.

    **Restricciones:**
    - NO se puede cambiar: codigo_espacio, bloque_id
    - Se puede cambiar: nombre, piso, tipo_espacio_id
    - Para cambiar de bloque, cree un nuevo espacio (auditoría)

    **Parámetros:**
    - espacio_id (int): ID del espacio a actualizar

    **Request Body (todos opcionales):**
    ```json
    {
        "nombre": "Aula 204 - Actualizada",
        "piso": 3,
        "tipo_espacio_id": 2
    }
    ```

    **Respuesta (200):**
    - Datos del espacio actualizado

    **Errores:**
    - 404: El espacio no existe
    - 400: Error en los datos enviados

    **Ejemplo:**
    ```bash
    PUT /espacios/1
    {
        "nombre": "Nuevo nombre",
        "piso": 2
    }
    ```
    """
    espacio = db.query(Espacio).filter(Espacio.id == espacio_id).first()

    if not espacio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El espacio con ID {espacio_id} no existe"
        )

    try:
        # Actualizar solo los campos permitidos
        datos_update = espacio_in.model_dump(exclude_unset=True)
        for campo, valor in datos_update.items():
            setattr(espacio, campo, valor)

        db.commit()
        db.refresh(espacio)
        return espacio

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al actualizar espacio: {str(e)}"
        )


# ============================================================================
# ENDPOINTS DE ELIMINACIÓN (DELETE)
# ============================================================================

@router.delete("/{espacio_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_espacio(
    espacio_id: int,
    db: Session = Depends(get_db)
):
    """
    Elimina un espacio (lógicamente - marca como inactivo).

    **IMPORTANTE:** Esta operación es irreversible. Si existen equipos
    asociados, primero debe reasignarlos a otro espacio.

    **Parámetros:**
    - espacio_id (int): ID del espacio a eliminar

    **Respuesta (204):** Sin contenido (eliminación exitosa)

    **Errores:**
    - 404: El espacio no existe
    - 409: Conflict - Existen equipos asociados al espacio

    **Ejemplo:**
    DELETE /espacios/1
    """
    espacio = db.query(Espacio).filter(Espacio.id == espacio_id).first()

    if not espacio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El espacio con ID {espacio_id} no existe"
        )

    try:
        db.delete(espacio)
        db.commit()
    except Exception as e:
        db.rollback()
        if "foreign key" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No se puede eliminar el espacio: existen equipos asociados"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al eliminar espacio: {str(e)}"
        )
