"""
Módulo de Endpoints para Autenticación.

Este módulo implementa los endpoints de seguridad para:
- Login: Validación de credenciales y generación de JWT
- Formato OAuth2: Soporta OAuth2PasswordRequestForm estándar

Arquitectura de Autenticación:
- Usa OAuth2 con contraseña (no es OAuth2 real, pero compatible con estándares)
- Genera JWT con claims: sub (email) y rol (tipo_rol.value)
- La contraseña se valida comparando hash con bcrypt
- Tokens expiran según ACCESS_TOKEN_EXPIRE_MINUTES en config

Seguridad:
- Validación de usuario existe (401 si no)
- Validación de contraseña (401 si falla)
- Validación de usuario activo (400 si está inactivo)
- Tokens con expiración automática
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.usuario import Token
from app.services import usuario as usuario_service
from app.core.security import verificar_contrasena, crear_token_acceso


# ============================================================================
# CONFIGURACIÓN DEL ROUTER
# ============================================================================

router = APIRouter(
    prefix="/auth",
    tags=["Autenticación"],
    responses={
        400: {"description": "Solicitud inválida o usuario inactivo"},
        401: {"description": "Credenciales inválidas (usuario no existe o contraseña incorrecta)"},
    },
)


# ============================================================================
# ENDPOINTS DE AUTENTICACIÓN
# ============================================================================


@router.post(
    "/login/access-token",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="Obtener token de acceso JWT",
    responses={
        200: {"description": "Token JWT generado exitosamente"},
        400: {"description": "Usuario inactivo"},
        401: {"description": "Credenciales inválidas"},
    },
)
def login_para_obtener_token_acceso(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:
    """
    Endpoint para login y obtención de token JWT.

    **OAuth2 PasswordRequestForm:**
    - username: Campo estándar OAuth2 que usamos para email del usuario
    - password: Contraseña en texto plano a validar

    **Flujo de Autenticación:**
    1. Extrae email desde form_data.username (estándar OAuth2)
    2. Busca usuario en BD por email
    3. Valida que usuario existe (401 si no)
    4. Valida que contraseña coincide con hash (401 si falla)
    5. Valida que usuario está activo (400 si está inactivo)
    6. Genera JWT con claims: sub (email), rol (tipo_rol.value)
    7. Retorna token JWT con tipo "bearer"

    **Parámetros (form-data OAuth2):**
    - username: Email del usuario (extraído desde form_data.username)
    - password: Contraseña en texto plano

    **Respuesta (Token):**
    - access_token: JWT firmado con información del usuario
    - token_type: "bearer" (tipo de autorización HTTP)

    **Códigos HTTP:**
    - 200: Autenticación exitosa, token generado
    - 400: Usuario inactivo en el sistema
    - 401: Credenciales inválidas (usuario no existe o password incorrecto)

    **Ejemplo de Solicitud (form-data):**
    ```
    POST /auth/login/access-token
    Content-Type: application/x-www-form-urlencoded

    username=tecnico@ucc.edu.co&password=MiPassword123
    ```

    **Ejemplo de Respuesta (200):**
    ```json
    {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer"
    }
    ```

    **Ejemplo de Respuesta (401 - Credenciales Inválidas):**
    ```json
    {
        "detail": "Email o contraseña incorrectos"
    }
    ```

    **Ejemplo de Respuesta (400 - Usuario Inactivo):**
    ```json
    {
        "detail": "Usuario inactivo en el sistema"
    }
    ```
    """

    # ========================================================================
    # 1. EXTRAER EMAIL DESDE form_data.username (estándar OAuth2)
    # ========================================================================

    # En OAuth2PasswordRequestForm, el campo "username" es obligatorio
    # Aquí lo usamos como email del usuario
    email = form_data.username
    contrasena = form_data.password

    # ========================================================================
    # 2. BUSCAR USUARIO POR EMAIL EN LA BASE DE DATOS
    # ========================================================================

    # Consulta a BD usando el servicio de usuario
    usuario = usuario_service.obtener_usuario_por_email(db, email)

    # ========================================================================
    # 3. VALIDAR QUE EL USUARIO EXISTE (Retornar 401 si no)
    # ========================================================================

    if not usuario:
        # Usuario no encontrado en BD
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},  # Requerido por OAuth2
        )

    # ========================================================================
    # 4. VALIDAR QUE LA CONTRASEÑA ES CORRECTA (Retornar 401 si falla)
    # ========================================================================

    # Comparar contraseña plana con hash almacenado usando bcrypt
    es_contrasena_correcta = verificar_contrasena(
        contrasena_plana=contrasena,
        contrasena_hasheada=usuario.hashed_password,
    )

    if not es_contrasena_correcta:
        # Contraseña no coincide con el hash en BD
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # ========================================================================
    # 5. VALIDAR QUE EL USUARIO ESTÁ ACTIVO (Retornar 400 si está inactivo)
    # ========================================================================

    if not usuario.activo:
        # Usuario existe pero está desactivado en el sistema
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario inactivo en el sistema",
        )

    # ========================================================================
    # 6. GENERAR JWT CON PAYLOAD: sub (email) y rol
    # ========================================================================

    # Preparar datos para incluir en el JWT
    # - sub: email del usuario (identificador único)
    # - rol: tipo_rol.value (valor del enum, ej: "Administrador", "Técnico")
    payload_jwt = {
        "sub": usuario.correo,                    # Email como identificador
        "rol": usuario.tipo_rol.value,            # Rol del usuario
    }

    # Crear token JWT con función de seguridad
    # La función crear_token_acceso maneja:
    # - Serialización del payload
    # - Tiempo de expiración automático
    # - Firma con SECRET_KEY
    # - Algoritmo especificado (HS256)
    access_token = crear_token_acceso(datos=payload_jwt)

    # ========================================================================
    # 7. RETORNAR TOKEN EN ESQUEMA Token
    # ========================================================================

    # Esquema Token contiene:
    # - access_token: JWT codificado
    # - token_type: "bearer" (tipo de autenticación HTTP)
    return Token(
        access_token=access_token,
        token_type="bearer",
    )

