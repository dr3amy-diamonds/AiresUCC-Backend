# AiresFlow API — Sistema de Gestión de Climatización UCC

**Transformando registros manuales en inteligencia de negocio.**
API RESTful + panel web que digitaliza, estructura y analiza los mantenimientos de la infraestructura térmica del campus Montería (Universidad Cooperativa de Colombia), eliminando la dependencia de bitácoras físicas y hojas de Excel fragmentadas.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.136-009688.svg?style=for-the-badge&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-12%2B-316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-3.0-150458.svg?style=for-the-badge&logo=pandas&logoColor=white)

## Tabla de contenido

1. [Qué es este proyecto](#qué-es-este-proyecto)
2. [Arquitectura](#arquitectura)
3. [Estructura del repositorio](#estructura-del-repositorio)
4. [Requisitos previos](#requisitos-previos)
5. [Ejecución paso a paso](#ejecución-paso-a-paso)
6. [Base de datos](#base-de-datos)
7. [API v1](#api-v1)
8. [Interfaz web](#interfaz-web)
9. [Roles y seguridad](#roles-y-seguridad)
10. [Pruebas](#pruebas)
11. [Solución de problemas](#solución-de-problemas)
12. [Documentación adicional](#documentación-adicional)

## Qué es este proyecto

AiresFlow nace de una problemática operativa real: pérdida de trazabilidad en los mantenimientos de aires acondicionados por el uso de bitácoras físicas y transcripciones en Excel. Este sistema crea una **única fuente de verdad** relacional y un motor analítico que genera KPIs estratégicos sobre los registros operativos.

Lógica de negocio destacada:

- **Semaforización proactiva:** endpoints de programaciones vencidas y pendientes (`/programaciones/estado/vencidas`, `/programaciones/estado/pendientes`) que evalúan los cronogramas en tiempo real.
- **Auto-programación algorítmica:** al cerrar un ticket (`cerrar_orden_atomica`), el sistema usa la `frecuencia_dias` del activo para insertar automáticamente la siguiente intervención.
- **Dashboard consolidado:** un endpoint (`/stats/*`) que orquesta consultas y cálculos con Pandas (`MaintenanceAnalytics`) y devuelve JSON listo para BI o para el panel web.
- **Auditoría caja negra:** toda mutación crítica se clasifica, narra y persiste en la tabla `auditoria` (snapshot de valores + actor + tipo de evento).

## Arquitectura

Arquitectura en capas con separación estricta de responsabilidades:

```
Navegador (frontend/ estático, Tailwind CDN)
        │  fetch JSON + JWT Bearer
        ▼
FastAPI  backend/app/main.py        rutas UI + archivos estáticos (/js /css /img)
        │
        ▼
API v1   backend/app/api/v1/        endpoints REST (auth, equipos, mantenimientos, …)
        │
        ▼
Servicios backend/app/services/     reglas de negocio, cerrar_orden_atomica,
        │                           MaintenanceAnalytics (Pandas), audit_* pipeline
        ▼
Modelos  backend/app/models/        SQLAlchemy 2.0  ─┐
Schemas  backend/app/schemas/       Pydantic v2      │
                                                     ▼
                                            PostgreSQL · esquema gestion_aires_ucc
```

Convenciones clave:

- **Validación en dos barreras:** Pydantic v2 valida y sanitiza el payload antes de tocar la lógica de negocio y antes de tocar la base de datos (igual que la firma mixta de endpoints `-> dict` que delegan en servicios).
- **Transacciones explícitas:** `SessionLocal` con `autocommit=False`; todo commit es explícito y hay rollback automático ante excepción (`backend/app/db/session.py`).
- **Integridad en BD:** el esquema define `UniqueConstraints`, `ForeignKeys` e índices (incluido un índice único parcial para una próxima programación pendiente por equipo/tipo) para que la base sea inmune a duplicados y errores de digitación típicos de Excel.
- **Enrutamiento semántico:** URLs limpias (`/inventario`) con alias legacy `.html` para evitar 404 en enlaces antiguos de la barra lateral (`backend/app/main.py`).
- **Auditoría en cadena:** `audit_classifier` → `audit_event_processor` → `audit_narrator` → `audit_presentacion` transforman cada evento de negocio en un registro legible para la bitácora de gestión.

Los nodos más centrales del sistema (extraídos del grafo de conocimiento del proyecto, `graphify-out/GRAPH_REPORT.md`, 1190 nodos / 2174 aristas / 77 comunidades) son: `Usuario`, `Equipo`, `Programacion`, `Mantenimiento`, `procesar_evento_auditoria()` y `MaintenanceAnalytics`. Esto confirma que el eje del sistema es el ciclo de vida activo → programación → mantenimiento → auditoría.

## Estructura del repositorio

```
├── backend/
│   ├── app/
│   │   ├── main.py                 # App FastAPI, CORS, middleware, rutas UI, estáticos
│   │   ├── api/v1/endpoints/       # 17 routers REST (auth, equipos, mantenimientos, …)
│   │   ├── core/security.py        # JWT (python-jose) + hashing bcrypt
│   │   ├── db/session.py           # Engine PostgreSQL, pool, get_db()
│   │   ├── models/                 # 14 modelos SQLAlchemy (esquema gestion_aires_ucc)
│   │   ├── schemas/                # Contratos Pydantic v2 de entrada/salida
│   │   └── services/               # Reglas de negocio + analytics Pandas + auditoría
│   ├── alembic/versions/           # Migraciones históricas 001–003 (referencia; ver Base de datos)
│   └── tests/test_implementation.py
├── frontend/                       # 11 páginas HTML + js/ + css/ + img/ (servidas por FastAPI)
├── database/                       # Script de esquema SQL (ver Base de datos)
├── graphify-out/                   # Grafo de conocimiento: GRAPH_REPORT.md, graph.html, graph.json
├── requirements.txt
├── PRODUCT.md / MEMORIA_CAMBIOS_2026-10-03.md
└── .env                            # NO versionado — debes crearlo (ver paso 4)
```

## Requisitos previos

| Componente | Versión | Notas |
|---|---|---|
| Python | 3.9+ (recomendado 3.11+) | Con `pip` y `venv` |
| PostgreSQL | 12+ | Local o remoto; debe existir el esquema `gestion_aires_ucc` |
| Cliente `psql` | opcional | Para cargar el esquema SQL |
| Git | — | Para clonar |

No se requiere Node.js ni compilación: el frontend es HTML/JS estático con Tailwind por CDN y lo sirve el propio FastAPI.

## Ejecución paso a paso

Los comandos asumen la raíz del repositorio como directorio de trabajo. En Windows se usa PowerShell; los equivalentes Linux/macOS van anotados.

### 1. Clonar e instalar dependencias

```powershell
git clone <URL_DEL_REPOSITORIO>
Set-Location <carpeta-del-proyecto>

python -m venv .venv
.\.venv\Scripts\Activate.ps1        # Linux/macOS: source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Si PowerShell bloquea la activación, ejecuta una vez: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

### 2. Crear la base de datos

Con PostgreSQL en marcha (base `aires_ucc` como ejemplo):

```powershell
psql -U postgres -c "CREATE DATABASE aires_ucc;"
psql -U postgres -d aires_ucc -f database/database.sql
```

El script crea el esquema `gestion_aires_ucc` con sus 14 tablas e índices. Detalles y alternativa en [Base de datos](#base-de-datos).

### 3. Crear el archivo `.env`

Crea el archivo `.env` en la **raíz del repositorio** (mismo nivel que `requirements.txt`). Lo leen `backend/app/db/session.py` y `backend/app/core/security.py`. Las cuatro variables son obligatorias: si falta alguna, la app no arranca (`KeyError`).

```dotenv
DATABASE_URL=postgresql://postgres:TU_PASSWORD@localhost:5432/aires_ucc
SECRET_KEY=REEMPLAZA_POR_UNA_CLAVE_ALEATORIA
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

Genera el `SECRET_KEY` con:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
# Linux/macOS alternativa: openssl rand -hex 32
```

### 4. Crear el primer usuario (obligatorio para iniciar sesión)

El login valida contra la tabla `encargados`. Inserta un usuario activo con la contraseña hasheada. Desde la carpeta `backend` y con el entorno virtual activo:

```powershell
Set-Location backend
python -c "from app.core.security import hashear_contrasena; print(hashear_contrasena('TuPasswordSegura123'))"
```

Copia el hash resultante y ejecútalo en PostgreSQL (ajusta correo y rol):

```sql
INSERT INTO gestion_aires_ucc.encargados
  (nombre, apellido, tipo_rol, telefono, correo_institucional, hashed_password, activo)
VALUES
  ('Admin', 'Sistema', 'Jefe de Infraestructura', '0000000000',
   'admin@ucc.edu.co', '<HASH_BCRYPT_AQUI>', true);
```

Roles permitidos: `Jefe de Infraestructura`, `Auxiliar de Infraestructura`, `Tecnico` (enum `TipoRol`).

### 5. Levantar el servidor

El paquete se importa como `app.*`, por lo que **uvicorn debe ejecutarse desde la carpeta `backend/`**:

```powershell
Set-Location backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Verificación rápida (deja el servidor corriendo en otra terminal):

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health-check
# Linux/macOS: curl http://127.0.0.1:8000/api/v1/health-check
```

### 6. Verificar login por API

```powershell
Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8000/api/v1/auth/login/access-token" `
  -ContentType "application/x-www-form-urlencoded" `
  -Body @{ username = "admin@ucc.edu.co"; password = "TuPasswordSegura123" }
```

Devuelve `{ "access_token": "...", "token_type": "bearer" }`. El frontend usa ese token en el header `Authorization: Bearer <token>`.

### 7. Abrir la interfaz web

Con el servidor arriba, abre en el navegador:

- `http://127.0.0.1:8000/` o `/login` — inicio de sesión.
- `http://127.0.0.1:8000/docs` — Swagger UI interactivo.
- `http://127.0.0.1:8000/redoc` — ReDoc.

El frontend espera la API exactamente en `http://127.0.0.1:8000/api/v1` (`frontend/js/config.js`). Si cambias host o puerto del backend, actualiza también esa constante.

## Base de datos

- **Motor:** PostgreSQL. **Esquema:** `gestion_aires_ucc` (definido en cada modelo con `__table_args__ = {"schema": "gestion_aires_ucc"}`).
- **Tablas (14):** `auditoria`, `bloques`, `componentes_usados`, `encargados` (usuarios), `equipos`, `espacios`, `mantenimientos`, `marcas`, `programaciones`, `tipos_componentes`, `tipos_equipos`, `tipos_espacios`, `tipos_gas_refrigerante`, `tipos_mantenimiento`.
- **Script canónico de creación:** `database/database.sql` (crea esquema, tablas, índices y restricciones únicas). Cárgalo con `psql -d <base> -f database/database.sql`.

> Nota: `database/database.sql` no está versionado en git. Si tu copia no lo incluye, solicítalo al equipo del proyecto; sin el esquema, la app arranca pero cualquier consulta fallará con `schema "gestion_aires_ucc" does not exist`.

- **Migraciones:** `backend/alembic/versions/` contiene 3 migraciones históricas de referencia (001: columnas `fecha_compra`, `voltaje`, `refrigerante` en `equipos`; 002: `tipo_evento` y `actor_nombre` en `auditoria`; 003: tabla `tipos_gas_refrigerante`). El CLI de Alembic **no está configurado para ejecutarse** (`backend/alembic.ini` está vacío y no existe `alembic/env.py`), así que no ejecutes `alembic upgrade head`: aplica estos cambios a mano solo si tu `database.sql` es anterior a ellos. Si el script base ya los incluye, no hay nada que hacer.
- **Conexión:** el pool usa `pool_pre_ping=True` y `pool_recycle=3600`, pensado para el timeout de PostgreSQL y recargas en desarrollo (`backend/app/db/session.py`).

## API v1

Prefijo global: `/api/v1`. Documentación interactiva en `/docs`.

| Recurso | Prefijo | Endpoints destacados |
|---|---|---|
| Autenticación | `/auth` | `POST /login/access-token` |
| Usuarios | `/usuarios` | CRUD; gestión de roles y estado activo |
| Equipos | `/equipos` | CRUD, cambio de estado, búsqueda por código, hoja de vida |
| Mantenimientos | `/mantenimientos` | CRUD, cierre de orden (dispara auto-programación) |
| Programaciones | `/programaciones` | `/estado/pendientes`, `/estado/vencidas`, `/estado/completadas`, `/mis-asignadas`, `/orden/{orden_id}`, `/analisis/resumen`, `/analisis/agrupar-por-estado`, `/{id}/completar`, `/{id}/cancelar` |
| Dashboard analítico | `/stats` | `/disponibilidad`, `/cumplimiento`, `/problematicos`, `/tecnicos`, `/exportar` |
| Dashboard resumen | `/dashboard` | `/resumen` |
| Calendario | `/calendario` | `/resumen` |
| Espacios / Bloques | `/espacios`, `/bloques` | CRUD; jerarquía bloque → piso → espacio |
| Marcas | `/marcas` | CRUD |
| Catálogos | `/tipos-equipo`, `/tipos-espacios`, `/tipos-mantenimiento`, `/tipos-gas-refrigerante`, `/tipo_componentes` | CRUD |
| Auditoría | `/auditoria` | Bitácora de gestión con filtros por bloque/piso/espacio |
| Sistema | — | `/api/v1/health-check`, `/health`, `/api/info` |

## Interfaz web

Servida por FastAPI desde `frontend/` (asset estático `frontend/img/ucc.png` para la marca UCC):

| Ruta limpia | Alias legacy | Vista |
|---|---|---|
| `/` , `/login` | `/auth_login.html` | Inicio de sesión |
| `/dashboard` | `/analytics_dashboard.html` | Indicadores y analítica |
| `/inventario` | `/asset_inventory.html` | Inventario y hoja de vida por equipo |
| `/programacion` | `/maintenance_scheduler.html` | Agenda operativa de servicios |
| `/calendario` | `/calendar.html` | Resumen anual tipo Excel |
| `/usuarios` | `/admin_access_control.html` | Control de acceso y roles |
| `/exportar` | `/data_export_center.html` | Centro de exportación de datos |
| `/auditoria` | `/maintenance_audit_logs.html` | Bitácora de eventos y gestión |
| `/reporte-tecnico` | `/service_report_form.html` | Cierre de orden e insumos |
| `/mis-ordenes` | `/mis_ordenes.html` | Agenda del técnico |
| `/perfil` | `/user_profile_settings.html` | Ajustes de cuenta |

## Roles y seguridad

- **Autenticación:** JWT firmado (`HS256` por defecto) con claims `sub` (correo) y `rol`; expiración según `ACCESS_TOKEN_EXPIRE_MINUTES`. Hashing de contraseñas con bcrypt (12 rounds). Dependencias `require_role(*roles)` y `get_current_user` protegen los endpoints (`backend/app/core/security.py`).
- **Roles (`TipoRol`):** `Jefe de Infraestructura` (máximos privilegios), `Auxiliar de Infraestructura` (privilegios limitados), `Tecnico` (operativo).
- **Middlewares:** limpieza automática de credenciales en query params (redirección transparente) y cabeceras `X-Content-Type-Options`, `X-Frame-Options`, `Cache-Control: no-store` (`backend/app/main.py`).
- **Auditoría:** las mutaciones críticas quedan registradas con snapshot de texto (bloque/piso/espacio) para que la bitácora no dependa de joins.

## Pruebas

El archivo `backend/tests/test_implementation.py` valida imports de modelos, seguridad, hashing, JWT, analytics y enums. Se ejecuta como script (no requiere pytest):

```powershell
Set-Location backend
python -m tests.test_implementation
```

Salida esperada: resumen con `Total | Exitosas | Fallidas` y `TODAS LAS PRUEBAS PASARON EXITOSAMENTE`.

Con pytest (opcional, instálalo aparte porque no viene en `requirements.txt`):

```powershell
pip install pytest
python -m pytest tests/test_implementation.py -v
```

## Solución de problemas

| Síntoma | Causa | Solución |
|---|---|---|
| `KeyError: 'DATABASE_URL'` al arrancar | No existe `.env` en la raíz o falta la variable | Crea `.env` con las 4 variables del paso 3 |
| `KeyError: 'SECRET_KEY'` / `'ALGORITHM'` / `'ACCESS_TOKEN_EXPIRE_MINUTES'` | Faltan variables obligatorias de seguridad | Añádelas al `.env` |
| `ModuleNotFoundError: No module named 'app'` | Uvicorn lanzado desde la raíz | Ejecuta desde `backend/`: `python -m uvicorn app.main:app --reload` |
| `psycopg2.OperationalError: connection refused` | PostgreSQL apagado o credenciales/host incorrectos | Arranca PostgreSQL y revisa `DATABASE_URL` |
| `schema "gestion_aires_ucc" does not exist` | No se cargó `database/database.sql` | Carga el script (sección Base de datos) |
| Login responde 401 aunque el usuario exista | Contraseña no coincide con el hash bcrypt | Re-genera el hash y actualiza `hashed_password` |
| Login responde 400 "Usuario inactivo" | `activo = false` en `encargados` | `UPDATE … SET activo = true` |
| Las páginas cargan pero los datos no | API no está en `http://127.0.0.1:8000` | Ajusta `API_BASE_URL` en `frontend/js/config.js` |
| 404 en `/inventario` u otra ruta UI | Falta la carpeta `frontend/` en la raíz | Verifica que `frontend/` exista junto a `backend/` |

## Documentación adicional

- `PRODUCT.md` — contexto de producto: usuarios, propósito, capacidades y principios.
- `MEMORIA_CAMBIOS_2026-10-03.md` — bitácora de cambios funcionales recientes (historial de intervenciones, estados del equipo).
- `graphify-out/GRAPH_REPORT.md` — auditoría del grafo de conocimiento del código (nodos centrales, comunidades, conexiones inesperadas).
- `http://127.0.0.1:8000/docs` — contrato OpenAPI en vivo.

---

**Institución:** Universidad Cooperativa de Colombia (UCC) — Montería
**Proyecto:** Formulación de Proyecto — Octavo Semestre
