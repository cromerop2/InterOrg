# Web · Copa Colegial

Interfaz HTML, CSS y JavaScript conectada a FastAPI. Se sirve desde el mismo
backend: no necesita un servidor de frontend ni una compilación.

Desde la raíz:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\Start-Backend.ps1
```

Abre http://127.0.0.1:8001. La base predeterminada es
`backend/campeonato_prueba_manual.sqlite3`, elegida por el script para las pruebas.
Si arrancas Uvicorn directamente, utiliza la base indicada por tu DATABASE_URL.

La vista pública consulta campeonato, fixture, posiciones por grupo, equipos y
plantillas. Se actualiza cada 30 segundos mientras está visible. No simula pagos,
eventos de árbitro ni goles individuales, porque esos endpoints no forman parte
del backend actual.

**Acceso administrador** permite iniciar sesión y administrar colegios, entrenadores,
equipos, jugadores, campeonatos, inscripciones, fixture, horarios y resultados.
La autorización también se comprueba en el servidor. La sesión se guarda en
sessionStorage y se elimina al cerrar sesión o recibir un 401.

El cliente `js/api.js` maneja peticiones, token, límites de espera y mensajes de
validación. Los resultados y posiciones se calculan en la API. Todas las mutaciones
se confirman en el servidor antes de actualizar la pantalla.

Para la prueba automatizada de navegador, consulta `mobile/README.md`.
