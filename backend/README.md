# Backend

Esta carpeta contiene el código fuente correspondiente al backend de la solución.

Debe incluir los servicios, APIs, lógica de negocio y demás componentes del lado del servidor utilizados por el proyecto.


# 🚀 Backend - API Torneo Colegial (FastAPI)

Servidor backend desarrollado en Python con **FastAPI** para la gestión integral del sistema de Torneo Colegial (Usuarios, Colegios, Equipos, Torneos, Partidos, Tabla de Posiciones y Pagos).

---

## 🛠️ Arquitectura y Estructura del Proyecto

El backend está organizado bajo una **Arquitectura en 3 Capas** (Vista/API, Lógica de Negocio y Persistencia):

```text
backend/app/
├── core/           # Enums (Roles, Estados de Torneo/Partido), seguridad y JWT
├── models/         # [PERSISTENCIA] Mapeo de tablas de la base de datos (SQLAlchemy)
├── schemas/        # [VISTA API] Validación de entradas y respuestas HTTP (Pydantic DTOs)
├── repositories/   # [PERSISTENCIA] Consultas directas a la base de datos
├── services/       # [LÓGICA DE NEGOCIO] Reglas del torneo, cálculo de puntos y fixtures
├── routers/        # [VISTA API] Endpoints HTTP de FastAPI (Controllers)
├── config.py       # Carga de variables de entorno
├── database.py     # Configuración y sesión de la base de datos
└── main.py         # Punto de entrada de la aplicación y configuración de CORS


# ⚙️ Requisitos Previos
Python 3.10+
Git

# 🚀 Instalación y Configuración Local
Sigue estos pasos para levantar el entorno de desarrollo local:

1. Navegar a la carpeta del backend

cd backend


2. Crear el entorno virtual

# En Windows (si `python` no funciona, usa `py`):
python -m venv .venv


3. Activar el entorno virtual

- Windows (PowerShell):

    .\.venv\Scripts\activate

- Git Bash / Linux / macOS:

    source .venv/bin/activate


4. Instalar dependencias

    pip install -r requirements.txt


5. Configurar variables de entorno
Crea una copia del archivo .env.example y llámalo .env:

cp .env.example .env

🏃‍♂️ Ejecución del Servidor
Para iniciar el servidor en modo desarrollo con recarga automática:

uvicorn app.main:app --reload



El servidor estará disponible en:

API Base: http://127.0.0.1:8000

Documentación Interactiva (Swagger UI): http://127.0.0.1:8000/docs

Documentación Alternativa (Redoc): http://127.0.0.1:8000/redoc