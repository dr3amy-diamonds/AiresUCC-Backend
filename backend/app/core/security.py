"""
Módulo de seguridad para autenticación y autorización.
Implementa funciones para hashear contraseñas y gestionar tokens JWT.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, List
import os
import bcrypt
from jose import JWTError, jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.usuario import Usuario
from app.services import usuario as usuario_service

# Cargar variables de entorno
load_dotenv()

# Configuración de JWT
SECRET_KEY: str = os.getenv("SECRET_KEY", "tu-clave-secreta-muy-segura-cambiar-en-produccion")
ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))


def hashear_contrasena(contrasena: str) -> str:
    """
    Hashea una contraseña en texto plano usando bcrypt directamente.

    Args:
        contrasena (str): Contraseña en texto plano.

    Returns:
        str: Contraseña hasheada como string.

    Ejemplo:
        >>> hashed = hashear_contrasena("mi_contraseña_123")
        >>> # El hash será diferente cada vez (bcrypt incluye salt)
    """
    # Convertir a bytes, hashear, y devolver como string
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(contrasena.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verificar_contrasena(contrasena_plana: str, contrasena_hasheada: str) -> bool:
    """
    Verifica que una contraseña en texto plano coincida con su hash bcrypt.

    Args:
        contrasena_plana (str): Contraseña en texto plano.
        contrasena_hasheada (str): Contraseña hasheada almacenada en la BD.

    Returns:
        bool: True si la contraseña es correcta, False en caso contrario.

    Ejemplo:
        >>> es_correcta = verificar_contrasena("mi_contraseña_123", hashed)
        >>> print(es_correcta)  # True
    """
    try:
        # Convertir hash a bytes si es string
        if isinstance(contrasena_hasheada, str):
            contrasena_hasheada = contrasena_hasheada.encode('utf-8')

        return bcrypt.checkpw(contrasena_plana.encode('utf-8'), contrasena_hasheada)
    except Exception:
        return False


def crear_token_acceso(
    datos: dict,
    expira_en: Optional[timedelta] = None
) -> str:
    """
    Crea un token de acceso JWT firmado.

    Args:
        datos (dict): Datos a incluir en el token (ej: {"sub": user_id}).
        expira_en (timedelta, opcional): Tiempo de expiración personalizado.
                                         Por defecto usa ACCESS_TOKEN_EXPIRE_MINUTES.

    Returns:
        str: Token JWT codificado.

    Ejemplo:
        >>> token = crear_token_acceso({"sub": "123", "tipo": "access"})
        >>> # Token válido durante 30 minutos (por defecto)
    """
    # Hacer copia para no mutar el diccionario original
    datos_copia = datos.copy()

    # Calcular tiempo de expiración
    if expira_en:
        tiempo_expiracion = datetime.now(timezone.utc) + expira_en
    else:
        tiempo_expiracion = datetime.now(timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )

    # Agregar claim de expiración
    datos_copia.update({"exp": tiempo_expiracion})

    # Firmar y codificar el token
    token_codificado = jwt.encode(
        datos_copia,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return token_codificado


def verificar_token(token: str) -> Optional[dict]:
    """
    Verifica y decodifica un token JWT.

    Args:
        token (str): Token JWT a verificar.

    Returns:
        Optional[dict]: Diccionario con los datos del token si es válido.
                        Retorna None si el token es inválido o expiró.

    Ejemplo:
        >>> datos = verificar_token(token)
        >>> if datos:
        ...     print(f"Usuario ID: {datos['sub']}")
        ... else:
        ...     print("Token inválido o expirado")
    """
    try:
        datos = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        return datos
    except JWTError:
        # Token inválido, expirado o no se pudo decodificar
        return None


def require_role(*allowed_roles: str):
    """
    Dependencia para verificar que el usuario autenticado tiene un rol permitido.
    
    Args:
        *allowed_roles: Roles permitidos (ej: "Tecnico", "Jefe de Infraestructura")
    
    Returns:
        Función dependencia que valida el rol del JWT
    
    Ejemplo de uso:
        @router.get("/", dependencies=[Depends(require_role("Tecnico", "Jefe de Infraestructura"))])
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    async def check_role(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
        """
        Valida que el token JWT contiene un rol permitido.
        """
        token = credentials.credentials

        # Verificar y decodificar el token
        datos_token = verificar_token(token)

        if not datos_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido o expirado",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Extraer rol del token
        rol_usuario = datos_token.get("rol")

        if not rol_usuario:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token no contiene información de rol",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Validar que el rol está en la lista de roles permitidos
        if rol_usuario not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado. Rol '{rol_usuario}' no tiene permisos para este recurso. Roles permitidos: {', '.join(allowed_roles)}"
            )

        # Retornar datos del token para uso posterior si es necesario
        return datos_token

    return check_role


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    db: Session = Depends(get_db),
) -> Usuario:
    """
    Dependencia que valida el JWT y retorna el usuario autenticado.

    El ID del técnico se obtiene desde current_user.id; nunca debe
    exponerse como parámetro de URL por motivos de seguridad.
    """
    datos_token = verificar_token(credentials.credentials)

    if not datos_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    correo = datos_token.get("sub")
    if not correo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token no contiene identificador de usuario",
            headers={"WWW-Authenticate": "Bearer"},
        )

    usuario = usuario_service.obtener_usuario_por_email(db, correo)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario inactivo en el sistema",
        )

    return usuario

