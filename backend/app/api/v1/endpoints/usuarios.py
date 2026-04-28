"""
Módulo de Endpoints para la Entidad Usuario.

Este módulo implementa las rutas CRUD para gestionar usuarios:
- Creación de nuevos usuarios con validación de email duplicado
- Listado paginado con metadatos
- Consulta individual por ID
- Actualización selectiva de campos

Arquitectura Limpia:
- Las rutas delegan lógica a servicios (app.services.usuario)
- Los esquemas Pydantic validan entrada/salida
- La capa de BD está abstraída mediante SQLAlchemy ORM
- Códigos HTTP semánticos: 201 Created, 400 Bad Request, 404 Not Found, 409 Conflict

Seguridad:
- Tipos de response_model: UsuarioResponse para NUNCA exponer hashed_password
- IntegrityError capturado y convertido a HTTP 409 por email duplicado
- Type hints en todas las dependencias
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.session import get_db
from app.schemas.usuario import (
    UsuarioCreate,
    UsuarioResponse,
    UsuarioUpdate,
    UsuarioListResponse,
)
from app.services import usuario as usuario_service


# ============================================================================
# CONFIGURACIÓN DEL ROUTER
# ============================================================================

router = APIRouter(
    prefix="/usuarios",
    tags=["Usuarios"],
    responses={
        404: {"description": "Usuario no encontrado"},
        409: {"description": "Conflicto: email duplicado o violación de integridad"},
    },
)


# ============================================================================
# ENDPOINTS CRUD
# ============================================================================


@router.post(
    "/",
    response_model=UsuarioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo usuario",
    responses={
        201: {"description": "Usuario creado exitosamente"},
        400: {"description": "Datos inválidos (validación Pydantic)"},
        409: {"description": "Email ya registrado (violación de restricción única)"},
    },
)
def crear_usuario(
    usuario_in: UsuarioCreate,
    db: Session = Depends(get_db),
) -> UsuarioResponse:
    """
    Crear un nuevo usuario en el sistema.

    **Flujo de Validación:**
    1. Pydantic valida: email (EmailStr), password (min 8 chars), nombre (1-100 chars)
    2. El servicio hashea la contraseña con bcrypt
    3. Se intenta persistir en BD con restricción UNIQUE en correo
    4. Si hay email duplicado, la BD lanza IntegrityError → HTTP 409

    **Campos Requeridos:**
    - nombre: Nombre completo (1-100 caracteres)
    - correo: Email institucional válido y único
    - password: Contraseña en texto plano (8-255 caracteres)
    - tipo_rol: Rol del usuario (Administrador, Técnico, Supervisor, Contratista)
    - activo: Estado del usuario (default: true)

    **Respuesta (UsuarioResponse):**
    - NUNCA incluye hashed_password por seguridad
    - Incluye: id, nombre, correo, tipo_rol, activo, created_at, updated_at

    **Códigos HTTP:**
    - 201: Usuario creado exitosamente
    - 400: Datos inválidos (email mal formado, password muy corto, etc)
    - 409: Email duplicado (ya existe en BD)

    **Ejemplo de Solicitud:**
    ```json
    {
        "nombre": "Juan García",
        "correo": "juan.garcia@ucc.edu.co",
        "password": "MiPassword123",
        "tipo_rol": "Técnico",
        "activo": true
    }
    ```

    **Ejemplo de Respuesta (201):**
    ```json
    {
        "id": 1,
        "nombre": "Juan García",
        "correo": "juan.garcia@ucc.edu.co",
        "tipo_rol": "Técnico",
        "activo": true,
        "created_at": "2024-01-15T10:30:00",
        "updated_at": "2024-01-15T10:30:00"
    }
    ```
    """
    try:
        # Llamar servicio para crear usuario
        db_usuario = usuario_service.crear_usuario(db, usuario_in)
        return db_usuario

    except IntegrityError as e:
        # Capturar violación de restricción UNIQUE en email
        db.rollback()

        # Verificar si el error es por email duplicado
        if "uq_usuario_correo" in str(e.orig) or "unique constraint" in str(e.orig).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"El email '{usuario_in.correo}' ya está registrado en el sistema",
            )

        # Para otros errores de integridad, retornar 400
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Violación de restricción de integridad en la base de datos",
        )


@router.get(
    "/",
    response_model=UsuarioListResponse,
    summary="Listar usuarios con paginación",
    responses={
        200: {"description": "Lista de usuarios obtenida correctamente"},
    },
)
def listar_usuarios(
    skip: int = Query(
        0,
        ge=0,
        description="Número de usuarios a saltar (OFFSET) para paginación",
    ),
    limit: int = Query(
        10,
        ge=1,
        le=100,
        description="Número máximo de usuarios a retornar (LIMIT)",
    ),
    db: Session = Depends(get_db),
) -> UsuarioListResponse:
    """
    Obtener un listado paginado de todos los usuarios del sistema.

    **Parámetros de Consulta:**
    - skip: Número de usuarios a saltar (default: 0)
    - limit: Máximo de usuarios a retornar (default: 10, máximo: 100)

    **Paginación:**
    - Utiliza OFFSET/LIMIT de PostgreSQL para eficiencia
    - Retorna total de registros para cálculo de páginas en frontend
    - Ordenamiento: Descendente por fecha de creación (más recientes primero)

    **Respuesta (UsuarioListResponse):**
    - total: Total de usuarios en la BD
    - page: Número de página calculado (skip / limit)
    - size: Cantidad de registros en esta página
    - items: Lista de UsuarioResponse (sin hashed_password)

    **Códigos HTTP:**
    - 200: Lista obtenida correctamente

    **Ejemplo de Solicitud:**
    ```
    GET /usuarios/?skip=0&limit=10
    ```

    **Ejemplo de Respuesta (200):**
    ```json
    {
        "total": 25,
        "page": 0,
        "size": 10,
        "items": [
            {
                "id": 25,
                "nombre": "Usuario Reciente",
                "correo": "reciente@ucc.edu.co",
                "tipo_rol": "Técnico",
                "activo": true,
                "created_at": "2024-01-15T10:30:00",
                "updated_at": "2024-01-15T10:30:00"
            },
            ...
        ]
    }
    ```
    """
    # Obtener usuarios paginados y total
    usuarios, total = usuario_service.obtener_usuarios(db, skip=skip, limit=limit)

    # Calcular número de página (para metadatos)
    page = skip // limit if limit > 0 else 0
    current_page_size = len(usuarios)

    return UsuarioListResponse(
        total=total,
        page=page,
        size=current_page_size,
        items=usuarios,
    )


@router.get(
    "/{usuario_id}",
    response_model=UsuarioResponse,
    summary="Obtener un usuario por ID",
    responses={
        200: {"description": "Usuario encontrado"},
        404: {"description": "Usuario no existe"},
    },
)
def obtener_usuario(
    usuario_id: int = Path(
        ...,
        gt=0,
        description="ID único del usuario a buscar",
    ),
    db: Session = Depends(get_db),
) -> UsuarioResponse:
    """
    Obtener los detalles completos de un usuario específico por su ID.

    **Parámetro de Ruta:**
    - usuario_id: Identificador único del usuario (debe ser > 0)

    **Validación:**
    - Si el usuario no existe, retorna 404 Not Found
    - Búsqueda indexada por PRIMARY KEY para máxima eficiencia

    **Respuesta (UsuarioResponse):**
    - Incluye: id, nombre, correo, tipo_rol, activo, created_at, updated_at
    - NUNCA incluye hashed_password

    **Códigos HTTP:**
    - 200: Usuario encontrado y retornado
    - 404: Usuario no existe en BD

    **Ejemplo de Solicitud:**
    ```
    GET /usuarios/1
    ```

    **Ejemplo de Respuesta (200):**
    ```json
    {
        "id": 1,
        "nombre": "Juan García",
        "correo": "juan.garcia@ucc.edu.co",
        "tipo_rol": "Técnico",
        "activo": true,
        "created_at": "2024-01-15T10:30:00",
        "updated_at": "2024-01-15T10:30:00"
    }
    ```

    **Ejemplo de Respuesta (404):**
    ```json
    {
        "detail": "Usuario con ID 999 no encontrado"
    }
    ```
    """
    # Buscar usuario en BD
    db_usuario = usuario_service.obtener_usuario_por_id(db, usuario_id)

    # Validar existencia
    if not db_usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario con ID {usuario_id} no encontrado",
        )

    return db_usuario


@router.put(
    "/{usuario_id}",
    response_model=UsuarioResponse,
    summary="Actualizar un usuario existente",
    responses={
        200: {"description": "Usuario actualizado exitosamente"},
        404: {"description": "Usuario no existe"},
        409: {"description": "Conflicto de integridad en datos"},
    },
)
def actualizar_usuario(
    usuario_id: int = Path(
        ...,
        gt=0,
        description="ID único del usuario a actualizar",
    ),
    usuario_update: UsuarioUpdate = Body(...),
    db: Session = Depends(get_db),
) -> UsuarioResponse:
    """
    Actualizar parcialmente los datos de un usuario existente.

    **Parámetro de Ruta:**
    - usuario_id: ID del usuario a actualizar

    **Cuerpo de Solicitud (UsuarioUpdate):**
    - Todos los campos son opcionales (permite sparse updates)
    - nombre: Nuevo nombre (opcional)
    - tipo_rol: Nuevo rol (opcional)
    - activo: Nuevo estado (opcional, true/false)
    - NOTA: No incluye password (usar endpoint separado si es necesario)

    **Flujo de Actualización:**
    1. Validar que el usuario existe (404 si no)
    2. Pydantic valida campos opcionales si están presentes
    3. El servicio aplica cambios selectivamente
    4. updated_at se actualiza automáticamente en BD
    5. Retorna objeto actualizado

    **Códigos HTTP:**
    - 200: Usuario actualizado exitosamente
    - 404: Usuario no existe
    - 409: Conflicto de integridad (ej: violación de UNIQUE)

    **Ejemplo de Solicitud (cambiar solo nombre):**
    ```json
    {
        "nombre": "Juan García López"
    }
    ```

    **Ejemplo de Solicitud (cambiar rol y desactivar):**
    ```json
    {
        "tipo_rol": "Supervisor",
        "activo": false
    }
    ```

    **Ejemplo de Respuesta (200):**
    ```json
    {
        "id": 1,
        "nombre": "Juan García López",
        "correo": "juan.garcia@ucc.edu.co",
        "tipo_rol": "Supervisor",
        "activo": false,
        "created_at": "2024-01-15T10:30:00",
        "updated_at": "2024-01-15T11:45:30"
    }
    ```
    """
    try:
        # Validar existencia del usuario
        db_usuario = usuario_service.obtener_usuario_por_id(db, usuario_id)

        if not db_usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Usuario con ID {usuario_id} no encontrado",
            )

        # Aplicar actualización
        db_usuario_actualizado = usuario_service.actualizar_usuario(
            db, db_usuario, usuario_update
        )

        return db_usuario_actualizado

    except IntegrityError as e:
        # Capturar violación de restricciones de integridad
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Conflicto de integridad: los datos proporcionados violan restricciones de la base de datos",
        )





