# AiresFlow Analytics API

**Transformando registros manuales en inteligencia de negocio.**
Una API RESTful diseñada para digitalizar, estructurar y analizar datos de mantenimiento de infraestructura térmica, eliminando la dependencia de hojas de cálculo fragmentadas.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.136-009688.svg?style=for-the-badge&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-12+-316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-Data_Analysis-150458.svg?style=for-the-badge&logo=pandas&logoColor=white)

## Resumen del Proyecto

AiresFlow nace de una problemática operativa real: la pérdida de trazabilidad en los mantenimientos de equipos de aire acondicionado debido al uso de bitácoras físicas y transcripciones en Microsoft Excel. Esta deuda técnica generaba datos corruptos, mantenimientos puramente reactivos y altos costos operativos.

Este proyecto backend soluciona el problema creando una única fuente de verdad (Single Source of Truth) mediante una base de datos relacional robusta. Además, incorpora un motor analítico que procesa los registros en tiempo real para generar KPIs estratégicos, preparando el terreno para futuros modelos de mantenimiento predictivo.

## Arquitectura y Decisiones Técnicas

El sistema fue diseñado con una arquitectura en capas, priorizando la **calidad del dato** y la separación de responsabilidades:

- **Data Modeling & ORM:** `SQLAlchemy 2.0` acoplado a `PostgreSQL`. Se diseñaron 14 modelos relacionales con restricciones de integridad estrictas (`UniqueConstraints`, `ForeignKeys`) para garantizar que la base de datos sea inmune a la duplicidad y a los errores de tipografía comunes en Excel.
- **Data Validation (ETL ligero):** `Pydantic v2` actúa como la primera barrera de limpieza. Valida, sanitiza y transforma los payloads entrantes antes de que interactúen con la lógica de negocio.
- **Analytics Engine:** Integración de `Pandas` en la capa de servicios (`MaintenanceAnalytics`). En lugar de sobrecargar la base de datos con agregaciones complejas, los datos históricos se procesan en memoria para calcular métricas como el ratio preventivo/correctivo y la salud global del parque térmico.
- **Seguridad y Auditoría:** Autenticación mediante `JWT` y hashing de contraseñas con `Bcrypt`. Se implementó un modelo de auditoría (Caja Negra) para rastrear mutaciones críticas en los registros.

## Lógica de Negocio Destacada

Más allá del CRUD tradicional, AiresFlow automatiza los siguientes procesos clave:

1. **Semaforización Proactiva:** Endpoints especializados (`/alertas/vencidas`, `/alertas/proximas`) que evalúan los cronogramas en tiempo real para alertar sobre SLA incumplidos.
2. **Auto-Programación Algorítmica:** Al cerrar un ticket de mantenimiento, el sistema utiliza la `frecuencia_dias` del activo para insertar automáticamente la siguiente intervención en la base de datos, creando un ciclo de vida continuo y autónomo.
3. **Dashboard Endpoint Consolidado:** Un único endpoint (`/stats`) que orquesta múltiples consultas y cálculos de Pandas, entregando un JSON estructurado listo para ser consumido por herramientas de BI o librerías de visualización en el frontend.

## Instalación y Entorno de Desarrollo

El proyecto está preparado para ser clonado y ejecutado en entornos locales.

```bash
# 1. Clonar el repositorio
git clone https://github.com/tu-usuario/AiresFlow-Backend.git
cd AiresFlow-Backend

# 2. Crear y activar entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# (Edita el archivo .env con tus credenciales de PostgreSQL)

# 5. Ejecutar migraciones de base de datos
alembic upgrade head

# 6. Levantar el servidor de desarrollo
uvicorn app.main:app --reload
```