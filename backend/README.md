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
```

# ⚙️ Requisitos Previos
Python 3.10+
Git

# 🚀 Instalación y Configuración Local
Sigue estos pasos para levantar el entorno de desarrollo local:

### 1. Navegar a la carpeta del backend

```text 
cd backend
```


### 2. Crear el entorno virtual

En Windows (si `python` no funciona, usa `py`):
```text 
python -m venv .venv
```

### 3. Activar el entorno virtual

- Windows (PowerShell):

```text 
.\.venv\Scripts\activate
```

- Git Bash / Linux / macOS:

```text 
source .venv/bin/activate
```


### 4. Instalar dependencias

```text 
pip install -r requirements.txt
```


### 5. Configurar variables de entorno
Crea una copia del archivo .env.example y llámalo .env:

```text 
cp .env.example .env
```

## 🏃‍♂️ Ejecución del Servidor
Para iniciar el servidor en modo desarrollo con recarga automática:

```text 
uvicorn app.main:app --reload
```



# El servidor estará disponible en:

API Base: http://127.0.0.1:8000

Documentación Interactiva (Swagger UI): http://127.0.0.1:8000/docs

Documentación Alternativa (Redoc): http://127.0.0.1:8000/redoc
## Autenticación y usuarios

1. Configura `backend/.env` a partir de `.env.example` (`DATABASE_URL` y `SECRET_KEY`).
2. Crea el primer administrador (solo una vez, desde `backend`): `python scripts/crear_admin.py`
3. Inicia sesión con `POST /auth/login` (JSON `email` y `password`); devuelve `access_token` y `rol`.
4. Envía el token en cada petición protegida: `Authorization: Bearer <access_token>`. En `/docs`, botón **Authorize**.
5. Solo un Administrador crea cuentas (`POST /usuarios/`) y las suspende (`PATCH /usuarios/{id}/estado`).

Para proteger una ruta nueva: `Depends(requerir_roles(RolEnum.ENTRENADOR))` (ver `app/core/dependencies.py`).
Si tu base de datos ya existía antes de la Fase 1, ejecuta `database/migraciones/001_fase1_usuarios.sql`.

## Permisos por ruta

| Ruta | Consultar (GET) | Crear / modificar |
|---|---|---|
| `/torneos`, `/torneos/{id}/fases`, `/fases/{id}` | Público (espectadores) | Administrador |
| `/colegios`, `/canchas` | Cualquier usuario con sesión | Administrador |
| `/usuarios` | Administrador (cada usuario ve solo su cuenta) | Administrador |

Un torneo nace en `Inscripciones`; sus datos y fases solo se editan en ese estado. El estado cambia con
`POST /torneos/{id}/finalizar` y `POST /torneos/{id}/cancelar`. Las tablas nuevas se crean solas al arrancar.

## Inscripción de equipos (Fase 3)

1. El Administrador crea el torneo y sus reglas: `min_jugadores` (11 por defecto), `max_jugadores` (25), `min_equipos` (2), `permite_transferencias` (false).
2. Un Entrenador inscribe su equipo (`POST /equipos/`, queda **Preinscrito**) y agrega jugadores (`POST /equipos/{id}/jugadores`).
3. El Entrenador reporta el pago (`POST /equipos/{id}/pagos`): el equipo pasa a **Pago_Pendiente**.
4. El Administrador valida (`PATCH /pagos/{id}/validar`, o `PATCH /equipos/{id}/auditar`). Aprobar exige el mínimo de jugadores y deja el equipo **Habilitado**; rechazar exige observaciones y lo devuelve a Preinscrito.
5. `POST /torneos/{id}/iniciar` exige el mínimo de equipos Habilitados, pasa el torneo a En_Curso y bloquea todas las plantillas.

| Ruta | Quién |
|---|---|
| `POST /equipos/`, jugadores (alta y baja), `POST /equipos/{id}/pagos` | Entrenador dueño del equipo |
| Ver un equipo, su plantilla y sus pagos | Administrador o entrenador dueño |
| `GET /torneos/{id}/equipos` | Cualquier usuario con sesión |
| Auditar, validar pagos, descalificar, sancionar, transferir, iniciar torneo, vincular entrenador | Administrador |

La categoría "Sub-N" limita la edad a N años cumplidos en la fecha de inicio del torneo; otras categorías no tienen límite.
Un mismo documento no puede estar activo en dos equipos del mismo torneo (sí en torneos distintos).
