"""
Capa de Servicios para la Entidad Usuario.

Este módulo encapsula toda la lógica de negocio relacionada con usuarios:
- Lectura de datos con filtros
- Paginación de resultados
- Creación con hashing de contraseñas
- Actualización con validaciones de integridad

Arquitectura: La lógica de negocio está separada de las rutas FastAPI.
Todos los datos pasan por validaciones Pydantic antes de llegar aquí.

NOTA: Las excepciones se lanzan desde aquí para que los endpoints
(routers) decidan cómo manejarlas (400, 409, 500, etc).
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func

from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate, UsuarioResponse
from app.core.security import hashear_contrasena


# ============================================================================
# FUNCIONES DE LECTURA (READ)
# ============================================================================

def obtener_usuario_por_id(db: Session, usuario_id: int) -> Optional[Usuario]:
    """
    Obtiene un usuario de la base de datos por su ID.

    Este método realiza una consulta simple y directa a la tabla usuario,
    filtrando por clave primaria. Es la operación más rápida para identificar
    un usuario específico (índice único garantizado).

    Args:
        db (Session): Sesión de SQLAlchemy para ejecutar la consulta.
        usuario_id (int): ID único del usuario a buscar.

    Returns:
        Optional[Usuario]: Objeto Usuario si existe, None en caso contrario.
                           Retorna None en lugar de lanzar excepción para
                           permitir manejo simplificado en endpoints.

    Integridad PostgreSQL:
        - Índice: PRIMARY KEY (id) garantiza búsqueda O(log n)
        - El ID nunca es None ni duplicado

    Ejemplo:
        >>> usuario = obtener_usuario_por_id(db, usuario_id=1)
        >>> if usuario:
        ...     print(f"Encontrado: {usuario.nombre}")
        ... else:
        ...     print("Usuario no existe")
    """
    return db.query(Usuario).filter(Usuario.id == usuario_id).first()


def obtener_usuario_por_email(db: Session, correo_institucional: str) -> Optional[Usuario]:
    """
    Obtiene un usuario de la base de datos por su correo institucional.

    La búsqueda por correo_institucional es crítica para autenticación (login) y validación
    de duplicados. PostgreSQL garantiza que cada correo es único mediante
    la restricción UniqueConstraint 'uq_encargado_correo'.

    Args:
        db (Session): Sesión de SQLAlchemy para ejecutar la consulta.
        correo_institucional (str): Correo institucional del usuario (validado por Pydantic como EmailStr).

    Returns:
        Optional[Usuario]: Objeto Usuario si existe, None en caso contrario.

    Integridad PostgreSQL:
        - Índice UNIQUE: uq_encargado_correo garantiza máximo 1 resultado
        - Correo es inmutable una vez creado (en lógica de negocio)
        - La comparación es case-sensitive según configuración de la BD

    Ejemplo:
        >>> usuario = obtener_usuario_por_email(db, "tecnico@ucc.edu.co")
        >>> if usuario:
        ...     print(f"¡Bienvenido {usuario.nombre}!")
    """
    return db.query(Usuario).filter(Usuario.correo_institucional == correo_institucional).first()


def obtener_usuarios(
    db: Session,
    skip: int = 0,
    limit: int = 10
) -> tuple[List[Usuario], int]:
    """
    Obtiene una lista paginada de usuarios de la base de datos.

    Implementa paginación con OFFSET/LIMIT para optimizar memoria en listados
    grandes. Retorna tanto la lista de usuarios como el total de registros
    para permitir que el frontend calcule páginas totales.

    Args:
        db (Session): Sesión de SQLAlchemy para ejecutar la consulta.
        skip (int): Número de registros a saltar (OFFSET).
                    Ejemplo: skip=20, limit=10 retorna registros 21-30.
                    Valor por defecto: 0 (comienza desde el inicio).
        limit (int): Máximo número de registros a retornar (LIMIT).
                     Valor por defecto: 10. Máximo recomendado: 100 (en endpoints).

    Returns:
        tuple[List[Usuario], int]: Una tupla (usuarios, total_count) donde:
                                   - usuarios: Lista de objetos Usuario
                                   - total_count: Total de usuarios en la BD

    Integridad PostgreSQL:
        - OFFSET/LIMIT es atómico en PostgreSQL (sin race conditions)
        - El total_count refleja el estado ACTUAL de la consulta
        - Si registros se eliminan entre consultas, total_count se ajusta

    Consideraciones de Rendimiento:
        - Skip grande (ej: 10000) es ineficiente. Usar cursor-based pagination
          en endpoints si necesitas grandes offsets.
        - limit=100 es máximo recomendado para no bloquear conexiones.

    Ejemplo:
        >>> usuarios, total = obtener_usuarios(db, skip=0, limit=10)
        >>> print(f"Mostrando 10 de {total} usuarios")
        >>> for usr in usuarios:
        ...     print(f"{usr.nombre} ({usr.correo})")
    """
    # Obtener total de usuarios antes de aplicar limit
    total = db.query(func.count(Usuario.id)).scalar() or 0

    # Ejecutar consulta paginada con orden consistente
    usuarios = (
        db.query(Usuario)
        .order_by(Usuario.created_at.desc())  # Descendente (más recientes primero)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return usuarios, total


# ============================================================================
# FUNCIONES DE CREACIÓN (CREATE)
# ============================================================================

def crear_usuario(db: Session, usuario_in: UsuarioCreate) -> Usuario:
    """
    Crea un nuevo usuario en la base de datos con contraseña hasheada.

    Este es uno de los métodos más críticos para la seguridad. Implementa
    el siguiente flujo:

    1. Convierte esquema Pydantic a diccionario
    2. Extrae y hashea la contraseña con bcrypt
    3. Elimina el password plano del diccionario (seguridad en memoria)
    4. Crea instancia SQLAlchemy
    5. Persiste en BD con manejo de errores de integridad

    Args:
        db (Session): Sesión de SQLAlchemy con transacción activa.
        usuario_in (UsuarioCreate): Esquema validado de Pydantic con:
                                     - nombre (1-30 chars)
                                     - apellido (1-30 chars)
                                     - correo_institucional (EmailStr validado)
                                     - telefono (7-12 chars)
                                     - codigo_universitario (opcional)
                                     - password (8-255 chars, a hashear)
                                     - tipo_rol (Enum validado)
                                     - activo (bool, default=True)

    Returns:
        Usuario: Objeto Usuario recién creado con:
                 - id (auto-generado por BD)
                 - created_at, updated_at (server-side timestamps)
                 - hashed_password (nunca password plano)

    Raises:
        IntegrityError: Si hay violación de restricciones:
                       - Correo duplicado (uq_usuario_correo)
                       - Otros errores de integridad de datos
                       Nota: PyPDantic previene inyecciones antes de llegar aquí

    Flujo de Seguridad Detallado:
        1. usuario_in.model_dump() convierte esquema a dict seguro
        2. password = datos.pop('password') extrae el password
        3. hashear_contrasena(password) lo convierte a bcrypt
           - Bcrypt genera diferente hash para mismo password
           - Hash almacenado en variable local (no global)
        4. del datos['password'] asegura que password no persista en memoria
        5. Usuario(**datos) crea instancia sin referencia al password
        6. db.add() + db.commit() persiste en BD

    Integridad PostgreSQL:
        - UniqueConstraint 'uq_usuario_correo' previene duplicados
        - Sequence para ID auto-incrementado
        - server_default con func.now() para timestamps (BD genera, no cliente)
        - hashed_password tiene índice para búsquedas rápidas

    Manejo de Errores:
        - IntegrityError capturado y re-lanzado para que endpoint maneje
        - db.rollback() limpia transacción en caso de fallo
        - Logs de auditoría pueden agregarse aquí en futuro

    Ejemplo:
        >>> from app.schemas.usuario import UsuarioCreate
        >>> nuevo_usuario = UsuarioCreate(
        ...     nombre="Juan García",
        ...     correo="juan@ucc.edu.co",
        ...     password="MiPassword123!",
        ...     tipo_rol="Técnico"
        ... )
        >>> usuario_creado = crear_usuario(db, nuevo_usuario)
        >>> print(f"Usuario {usuario_creado.id} creado exitosamente")
    """
    try:
        # Convertir esquema Pydantic a diccionario
        datos = usuario_in.model_dump()

        # Extraer password antes de crear el usuario
        password = datos.pop("password")

        # Hashear la contraseña con bcrypt
        hashed_password = hashear_contrasena(password)

        # Eliminar referencia al password plano (seguridad en memoria)
        # (Nota: ya fue eliminado por pop(), pero explícito por claridad)
        datos["hashed_password"] = hashed_password

        # Crear instancia SQLAlchemy
        db_usuario = Usuario(**datos)

        # Agregar a sesión
        db.add(db_usuario)

        # Confirmar transacción
        db.commit()

        # Refrescar objeto para obtener ID autogenerado y timestamps
        db.refresh(db_usuario)

        return db_usuario

    except IntegrityError as e:
        # Rollback en caso de violación de restricciones
        db.rollback()

        # Re-lanzar la excepción para que el endpoint maneje
        # (ej: convertiéndola en HTTP 409 Conflict si es duplicate email)
        raise IntegrityError(
            statement="Fallo al crear usuario",
            params={"correo_institucional": usuario_in.correo_institucional},
            orig=e.orig
        ) from e


# ============================================================================
# FUNCIONES DE ACTUALIZACIÓN (UPDATE)
# ============================================================================

def actualizar_usuario(
    db: Session,
    db_obj: Usuario,
    obj_in: UsuarioUpdate
) -> Usuario:
    """
    Actualiza un usuario existente con validaciones de integridad.

    Este método permite actualizar selectivamente campos del usuario:
    - nombre, tipo_rol, activo (cambios simples)
    - password (si se incluye, debe ser hasheado)

    La estrategia es "actualización selectiva": solo los campos presentes
    en UsuarioUpdate se modifican. Los campos ausentes (None) se ignoran.

    Args:
        db (Session): Sesión de SQLAlchemy con transacción activa.
        db_obj (Usuario): Objeto Usuario actual obtenido de la BD.
                          Este es el objeto a modificar IN-PLACE.
        obj_in (UsuarioUpdate): Esquema de cambios con campos opcionales:
                                - nombre: Optional[str]
                                - tipo_rol: Optional[TipoRolSchema]
                                - activo: Optional[bool]
                                Nota: NO incluye password (endpoint separado)

    Returns:
        Usuario: El mismo objeto Usuario después de actualización,
                 con updated_at refrescado por la BD.

    Raises:
        IntegrityError: Si hay violación de restricciones (ej: correo duplicado
                       en UsuarioUpdate futuro si se agregase email).
        ValueError: Si se intenta cambiar forbidden fields (none actualmente).

    Flujo de Actualización:
        1. Convertir esquema actualización a diccionario
        2. Iterar solo campos NO-None (permitint sparse updates)
        3. Usar setattr() para modificación dinámica
        4. Haeshear password si está en actualizaciónes
        5. db.commit() persiste cambios
        6. db.refresh() obtiene updated_at de la BD

    Consideraciones de Auditoría:
        - updated_at se actualiza automáticamente en BD (func.now())
        - Cambios sensibles (ej: rol) pueden auditarse en futuro

    Integridad PostgreSQL:
        - UniqueConstraint previene duplicados en campos únicos
        - updated_at es server-side timestamp (no cliente)
        - Transacción atómica garantiza consistencia

    Ejemplo Casos de Uso:
        # Cambiar solo nombre
        >>> actualizar = UsuarioUpdate(nombre="Juan Modificado")
        >>> usuario_actualizado = actualizar_usuario(db, usuario, actualizar)

        # Cambiar rol
        >>> actualizar = UsuarioUpdate(tipo_rol="Supervisor")
        >>> usuario_actualizado = actualizar_usuario(db, usuario, actualizar)

        # Desactivar usuario
        >>> actualizar = UsuarioUpdate(activo=False)
        >>> usuario_actualizado = actualizar_usuario(db, usuario, actualizar)

        # Cambio múltiple
        >>> actualizar = UsuarioUpdate(nombre="Nuevo", activo=False)
        >>> usuario_actualizado = actualizar_usuario(db, usuario, actualizar)
    """
    try:
        # Convertir esquema a diccionario, excluyendo campos None
        datos = obj_in.model_dump(exclude_unset=True)

        # Iterar sobre cambios permitidos
        for campo, valor in datos.items():
            # Si el campo es password, hashearlo antes de assignar
            # (Nota: En UsuarioUpdate NO está password, pero lo dejamos
            #  por si en futuro se agrega endpoint de cambio desde admin)
            if campo == "password" and valor is not None:
                valor = hashear_contrasena(valor)
                campo = "hashed_password"

            # Asignar dinámicamente al objeto
            setattr(db_obj, campo, valor)

        # Confirmar transacción
        db.commit()

        # Refrescar para obtener updated_at actualizado en BD
        db.refresh(db_obj)

        return db_obj

    except IntegrityError as e:
        # Rollback en caso de violación de restricciones
        db.rollback()

        # Re-lanzar la excepción para que el endpoint maneje
        raise IntegrityError(
            statement="Fallo al actualizar usuario",
            params={"usuario_id": db_obj.id},
            orig=e.orig
        ) from e


# ============================================================================
# FUNCIONES AUXILIARES (UTILITIES)
# ============================================================================

def usuario_existe(db: Session, correo_institucional: str, excluir_id: Optional[int] = None) -> bool:
    """
    Verifica si un correo institucional ya está registrado en la BD (útil para validaciones).

    Usado en endpoints para prevenir duplicados antes de intentar crear.

    Args:
        db (Session): Sesión de SQLAlchemy.
        correo_institucional (str): Correo institucional a verificar.
        excluir_id (Optional[int]): Si se proporciona, excluye ese ID de la búsqueda
                                    (útil en updates para permitir mantener el email).

    Returns:
        bool: True si el correo ya existe en BD, False en caso contrario.

    Ejemplo:
        >>> if usuario_existe(db, "juan@ucc.edu.co"):
        ...     return HTTPException(400, "Email ya registrado")
    """
    query = db.query(Usuario).filter(Usuario.correo_institucional == correo_institucional)

    if excluir_id is not None:
        query = query.filter(Usuario.id != excluir_id)

    return query.first() is not None


def obtener_usuarios_activos(
    db: Session,
    skip: int = 0,
    limit: int = 10
) -> tuple[List[Usuario], int]:
    """
    Obtiene usuarios activos con paginación.

    Alternativa a obtener_usuarios() que filtra solo usuarios con activo=True.

    Args:
        db (Session): Sesión de SQLAlchemy.
        skip (int): Número de registros a saltar.
        limit (int): Máximo de registros a retornar.

    Returns:
        tuple[List[Usuario], int]: (usuarios_activos, total_activos)

    Ejemplo:
        >>> usuarios, total = obtener_usuarios_activos(db, skip=0, limit=10)
        >>> print(f"{len(usuarios)} activos de {total} totales")
    """
    total = db.query(func.count(Usuario.id)).filter(Usuario.activo == True).scalar() or 0

    usuarios = (
        db.query(Usuario)
        .filter(Usuario.activo == True)
        .order_by(Usuario.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return usuarios, total


def obtener_usuarios_por_rol(
    db: Session,
    tipo_rol: str,
    skip: int = 0,
    limit: int = 10
) -> tuple[List[Usuario], int]:
    """
    Obtiene usuarios filtrados por rol específico con paginación.

    Útil para listados administrativos (ej: "mostrar todos los técnicos").

    Args:
        db (Session): Sesión de SQLAlchemy.
        tipo_rol (str): Tipo de rol a filtrar (debe ser valor válido de TipoRol).
        skip (int): Número de registros a saltar.
        limit (int): Máximo de registros a retornar.

    Returns:
        tuple[List[Usuario], int]: (usuarios_del_rol, total_del_rol)

    Ejemplo:
        >>> tecnicos, total = obtener_usuarios_por_rol(db, "Técnico")
        >>> print(f"Total de técnicos: {total}")
    """
    total = (
        db.query(func.count(Usuario.id))
        .filter(Usuario.tipo_rol == tipo_rol)
        .scalar() or 0
    )

    usuarios = (
        db.query(Usuario)
        .filter(Usuario.tipo_rol == tipo_rol)
        .order_by(Usuario.nombre)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return usuarios, total

