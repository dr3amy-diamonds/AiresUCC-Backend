
-- 1. Marcas de los equipos (Exclusivo aires acondicionados)
-- Catálogo de fabricantes para estandarizar el registro y facilitar filtros en el frontend.
CREATE TABLE marcas (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(20) NOT NULL UNIQUE -- Evita duplicados como 'LG' y 'lg'. Clave para dropdowns en el UI.
);

-- 2. Categorías de lugares (Aula, Laboratorio, etc.)
-- Define el uso del espacio físico. Útil para métricas de impacto (ej. priorizar aulas sobre oficinas).
CREATE TABLE tipos_espacios (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE -- Estandariza la nomenclatura de la sede.
);

-- 3. Categorías de aires (Mini-split, Central, etc.)
-- Clasificación técnica indispensable para asignar el tipo de mantenimiento correcto.
CREATE TABLE tipos_equipos (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(30) NOT NULL UNIQUE
);

-- 4. Tipos de visitas técnicas
-- Define si es preventivo, correctivo, etc. Base para la generación automática de cronogramas.
CREATE TABLE tipos_mantenimiento (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(30) NOT NULL UNIQUE,
    frecuencia_dias INTEGER -- Crítico para FastAPI: usado por workers para calcular la próxima fecha de mantenimiento.
);

-- 5. Repuestos e insumos
-- Inventario de partes. Permite costeo de mantenimientos y proyecciones de presupuesto.
CREATE TABLE tipos_componentes (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(60) NOT NULL UNIQUE,
    unidad_medida VARCHAR(35) -- Define si se cuenta por unidad, metros, litros, etc.
);

-- 6. Los edificios de la universidad
-- Agrupación macro de la ubicación. Facilita la logística de las rutas de los técnicos.
CREATE TABLE bloques (
    id SERIAL PRIMARY KEY,
    codigo_bloque VARCHAR(15) NOT NULL UNIQUE,
    nombre_bloque VARCHAR(65) NOT NULL UNIQUE
);

-- 7. Los salones u oficinas
-- Ubicación exacta del equipo dentro del campus.
CREATE TABLE espacios (
    id SERIAL PRIMARY KEY,
    codigo_espacio VARCHAR(20) NOT NULL UNIQUE, -- Identificador físico en la puerta del salón.
    nombre VARCHAR(65) NOT NULL,
    piso INTEGER, -- Ayuda a visualizar la distribución vertical en mapas o dashboards.
    
    -- Puentes (Garantizan que un salón pertenece a un edificio y tipo válido)
    bloque_id INTEGER NOT NULL REFERENCES bloques(id),
    tipo_espacio_id INTEGER NOT NULL REFERENCES tipos_espacios(id)
);

-- 8. El personal técnico y administrativo
-- Gestión de usuarios que interactuarán con el sistema.
CREATE TABLE encargados (
    id SERIAL PRIMARY KEY,
    codigo_universitario INTEGER NOT NULL UNIQUE, -- ID institucional para cruce con RRHH.
    nombre VARCHAR(30) NOT NULL,
    apellido VARCHAR(30) NOT NULL,
    tipo_rol VARCHAR(50) NOT NULL
        CHECK (tipo_rol IN ('Tecnico interno', 'Supervisor', 'Administrador', 'Contratista', 'Solo lectura')), -- Control de RBAC estricto a nivel BD para la API.
    telefono VARCHAR(12) NOT NULL,
    correo_institucional VARCHAR(50) -- Clave para el envío de notificaciones y alertas desde Python.
);

-- 9. Los equipos (Aires acondicionados)
-- El "Activo" central del sistema. Cada registro es un aire físico real en la universidad.
CREATE TABLE equipos (
    id SERIAL PRIMARY KEY,
    codigo_activo VARCHAR(50) NOT NULL UNIQUE, -- Plaqueta de inventario oficial de la UCC.
    modelo VARCHAR(50),
    capacidad_btu INTEGER NOT NULL, -- Dato técnico vital para estimar consumo energético.
    fecha_instalacion DATE, -- Base para el cálculo de depreciación y vida útil.
    estado VARCHAR(20) DEFAULT 'Operativo'
        CHECK (estado IN ('Operativo', 'En reparacion', 'Inactivo', 'Dado de baja')), -- Evita estados basura. KPI principal para el dashboard de disponibilidad.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Puentes (Restringen la asignación a catálogos existentes)
    marca_id INTEGER NOT NULL REFERENCES marcas(id),
    tipo_equipo_id INTEGER NOT NULL REFERENCES tipos_equipos(id),
    espacio_id INTEGER NOT NULL REFERENCES espacios(id)
);

-- 10. Historial de mantenimientos reales
-- Bitácora inmutable de lo que ya sucedió. Fundamental para auditorías de calidad.
CREATE TABLE mantenimientos (
    id SERIAL PRIMARY KEY,
    fecha_mantenimiento DATE NOT NULL, -- Fecha real de ejecución. Sirve para resetear contadores en el backend.
    detalle_mantenimiento TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Puentes
    equipo_id INTEGER NOT NULL REFERENCES equipos(id), -- Vincula el trabajo al aire físico.
    encargado_id INTEGER NOT NULL REFERENCES encargados(id), -- Técnico que hizo el trabajo (responsabilidad directa).
    tipo_mantenimiento_id INTEGER NOT NULL REFERENCES tipos_mantenimiento(id),
    registrado_por INTEGER NOT NULL REFERENCES encargados(id) -- Quién digitó el dato en el sistema (trazabilidad).
);

-- 11. Componentes usados en cada mantenimiento (Tabla puente)
-- Detalle de los repuestos consumidos. Crucial para costear cada mantenimiento.
CREATE TABLE componentes_usados (
    id SERIAL PRIMARY KEY,
    cantidad NUMERIC(3,1) NOT NULL,
    precio_unitario NUMERIC(10,2), -- Captura el precio en el momento del uso para evitar distorsión por inflación.
    
    -- Puentes
    mantenimiento_realizado_id INTEGER NOT NULL REFERENCES mantenimientos(id),
    repuesto_utilizado_id INTEGER NOT NULL REFERENCES tipos_componentes(id)
);

-- 12. Programación de próximas citas
-- Agenda de mantenimiento futuro. La API consultará esta tabla a diario para lanzar alertas.
CREATE TABLE programaciones (
    id SERIAL PRIMARY KEY,
    fecha_programada DATE NOT NULL, -- Deadline de ejecución. Usado por la API para marcar atrasos.
    estado VARCHAR(20) NOT NULL DEFAULT 'Pendiente'
        CHECK (estado IN ('Pendiente', 'Completado', 'Cancelado', 'Vencido')), -- Máquina de estados controlada por la BD y procesada por FastAPI.
    
    -- Puentes
    equipo_id INTEGER NOT NULL REFERENCES equipos(id),
    tipo_mantenimiento_id INTEGER NOT NULL REFERENCES tipos_mantenimiento(id),
    
    -- Cierre del ciclo y rastreo
    mantenimiento_id INTEGER REFERENCES mantenimientos(id), -- Cuando se completa, se enlaza al reporte real de ejecución.
    observaciones TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 13. Auditoría del sistema (La caja negra)
-- Historial a prueba de manipulaciones para saber quién cambió qué.
CREATE TABLE auditoria (
    id SERIAL PRIMARY KEY,
    tabla_afectada VARCHAR(60) NOT NULL,
    registro_id INTEGER NOT NULL,
    campo VARCHAR(60) NOT NULL,
    valor_anterior TEXT,
    valor_nuevo TEXT,
    fecha_cambio TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Puente
    encargado_id INTEGER REFERENCES encargados(id) -- Usuario autenticado en el token JWT del backend.
);