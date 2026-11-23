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

## Programación de partidos (Fase 4A)

1. Con el torneo **En_Curso**, el Administrador arma los grupos de la fase de grupos: `POST /fases/{id}/grupos` con `{"grupos": {"Grupo A": [1, 2, 3]}}`.
2. Programa cruces con `POST /partidos/` (fase, equipos Habilitados, cancha, `fecha_hora` local sin zona horaria, árbitro opcional). Se valida que:
   las fechas estén dentro del torneo, la fase anterior haya finalizado, en grupos ambos equipos compartan grupo, la pareja no se repita en la fase,
   y que cancha, equipos y árbitro no se crucen con otro partido (dos partidos se cruzan si empiezan con menos de `duracion_partido_min` minutos de diferencia; 90 por defecto).
3. Cada partido nace con su marcador 0-0. Se puede `reprogramar`, `suspender` (libera el horario) y asignar árbitro (`PUT /partidos/{id}/arbitro`).
4. Cada entrenador envía su planilla con `PUT /partidos/{id}/equipos/{id_equipo}/alineacion` (si ya había una, la reemplaza mientras el partido esté Programado).
   Reglas del torneo: `titulares` (11) exactos y `max_suplentes` (7); los jugadores deben ser del equipo, estar activos y no sancionados.
5. Consultas: calendario de la fase (público), `GET /equipos/{id}/calendario`, `GET /partidos/mis-asignaciones` (árbitro), `GET /canchas/{id}/agenda?fecha=`.

`BCRYPT_ROUNDS` (12 por defecto) en el `.env` controla el costo de encriptar contraseñas; las pruebas lo bajan a 4.

## El día del partido (Fase 4B)

1. El árbitro designado inicia el partido (`POST /partidos/{id}/iniciar`); exige la alineación de ambos equipos. Si un equipo no la envió, el Administrador puede decretar W.O. (`POST /partidos/{id}/walkover`, marcador 3-0).
2. Con el partido En_Juego, el árbitro registra eventos (`POST /partidos/{id}/eventos`): gol, asistencia, tarjetas, sustitución y autogol.
   Se validan contra la alineación: quien marca debe estar en el campo, quien entra en una sustitución debe ser un suplente que no haya jugado, quien sale debe estar en el campo, y no se supera `max_sustituciones` (5 por defecto).
   Un gol o autogol actualiza el marcador solo; una tarjeta roja expulsa al jugador y lo deja **sancionado** hasta que el Administrador levante la sanción. Un evento por error se borra con `DELETE` y se revierte su efecto.
3. El árbitro puede fijar el marcador (`PUT /partidos/{id}/marcador`; los penales solo en eliminatorias) y cierra el acta (`POST /partidos/{id}/cerrar`).
   Al cerrar, el partido queda Finalizado, el resultado definitivo y la tabla de posiciones al día. En una eliminatoria empatada se exigen penales con un ganador.
4. Tabla de posiciones: puntos (`puntos_victoria` 3, `puntos_empate` 1), diferencia de goles, goles a favor y, si siguen empatados, el enfrentamiento directo.
5. El Administrador cierra cada grupo (`POST /tablas/{id}/cerrar`, requiere que todas las parejas hayan jugado) y luego la fase (`POST /fases/{id}/cerrar`), lo que habilita la siguiente.
   `GET /fases/{id}/clasificados` devuelve quiénes avanzan (`clasifican_por_grupo`, 2 por defecto, o los ganadores de la eliminatoria).
6. Público: minuto a minuto (`GET /partidos/{id}/eventos`), tablas y goleadores (`GET /torneos/{id}/goleadores`, solo partidos Finalizados; los autogoles no cuentan).
   El entrenador ve las estadísticas de su equipo en `GET /equipos/{id}/estadisticas`.
