# AiresFlow Backend - UCC Montería

AiresFlow es el núcleo (Backend) de la plataforma de gestión y analítica para el mantenimiento de sistemas de climatización de la Universidad Cooperativa de Colombia, Campus Montería. Este sistema trasciende el registro básico, integrando lógica de negocio avanzada y ciencia de datos para optimizar la vida útil de los activos institucionales.

---

## Objetivo del Proyecto

Digitalizar el flujo de trabajo de mantenimiento (preventivo y correctivo), eliminando la dependencia de registros físicos y proporcionando al Jefe de Infraestructura una herramienta de toma de decisiones basada en datos reales y trazabilidad total.

---

## Stack Tecnológico

- **Framework:** FastAPI (Asíncrono, alto rendimiento).
- **ORM:** SQLAlchemy 2.0 (Mapeo de datos moderno).
- **Base de Datos:** PostgreSQL.
- **Procesamiento de Datos:** Pandas (Generación de KPIs y métricas).
- **Seguridad:** JWT (JSON Web Tokens) & Bcrypt (Hashing de alta seguridad).
- **Validación:** Pydantic v2.

---

## Arquitectura del Sistema

El proyecto sigue una Arquitectura Modular, garantizando que el sistema sea escalable y fácil de mantener:

```
backend/
├── app/
│   ├── api/          # Endpoints de la API REST
│   ├── core/         # Configuración global y seguridad (JWT)
│   ├── db/           # Conexión y base de datos
│   ├── models/       # Modelos de SQLAlchemy (Tablas)
│   ├── schemas/      # Modelos de Pydantic (Validación)
│   └── services/     # Lógica de negocio y Analytics (Pandas)
```

---

## Características Implementadas (WIP)

Actualmente, el backend cuenta con los cimientos operativos listos:

- **Gestión de Activos:** Modelado completo de equipos, marcas y espacios con integridad referencial.
- **Seguridad y RBAC:** Sistema de autenticación con Roles (Administrador, Técnico, Supervisor, Contratista).
- **Motor de Analítica:** Implementación inicial de `MaintenanceAnalytics` usando Pandas para el cálculo de disponibilidad y salud del parque térmico.
- **Auditoría:** Registro de trazabilidad para cambios críticos en el inventario.

---

## Roadmap (Próximos Pasos)

### Corto Plazo (Prioridad Operativa)

- [ ] **Sistema de Notificaciones Híbrido:** Implementación de alertas web y notificaciones por correo para mantenimientos vencidos.
- [ ] **Módulo de Auditoría Visual:** Interfaz para rastrear cambios en los activos (Caja Negra).

### Mediano Plazo (Análisis y Seguridad)

- [ ] **Exportación Inteligente:** Generador de archivos CSV/Excel optimizados para ingesta en Power BI.
- [ ] **Seguridad 2FA:** Implementación de autenticación de dos factores para cuentas administrativas.

---

## Instalación (Entorno de Desarrollo)

1. Clonar el repositorio:

```bash
git clone https://github.com/tu-usuario/AiresFlow-Backend.git
```

2. Crear entorno virtual:

```bash
python -m venv venv
source venv/bin/scripts/activate  # En Windows: venv\Scripts\activate
```

3. Instalar dependencias:

```bash
pip install -r requirements.txt
```

4. Configurar variables de entorno: Crear un archivo `.env` basado en `.env.example` con tus credenciales de PostgreSQL y `SECRET_KEY`.

---

## Autor

**Valentina Ojeda Pascasio**  
Estudiante de Ingeniería de Sistemas - Universidad Cooperativa de Colombia  
Montería, Córdoba.

---

*Este proyecto es propiedad intelectual para la gestión de infraestructura de la UCC Montería.*