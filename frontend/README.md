# Frontend

Aplicación web (HTML + CSS + JavaScript sin framework, iconos Lucide por CDN). **No usa datos de ejemplo:** todo se obtiene de la API con `fetch`.

## Ejecutar

Desde `backend` (con la API configurada, ver `backend/README.md`): `uvicorn app.main:app --reload` y abrir http://127.0.0.1:8000/. FastAPI sirve esta carpeta en `/`, así que la API y la página comparten origen. Para apuntar a otra dirección, define `window.API_BASE = "https://…"` antes de cargar `js/script.js`.

## Pantallas

| Pantalla | Sesión | Qué hace |
|---|---|---|
| Dashboard público | No necesita | Torneo/fase, partido destacado, tablas por grupo, goleadores y próximos partidos. Se refresca cada 15 s. |
| Planilla del árbitro | Árbitro | Sus partidos asignados: iniciar, reloj, gol/tarjetas/cambio con la alineación oficial, borrar eventos y cerrar el acta. |
| Panel del entrenador | Entrenador | Inscribir equipo y jugadores, dar de baja, reportar pago, ver el calendario y enviar la planilla de cada partido. |
| Panel admin | Administrador | Torneos y fases, grupos y fixture automático, reprogramar/suspender/W.O., cerrar grupos y fases, canchas, colegios, validación de pagos y cuentas. |

El token JWT se guarda en `sessionStorage` y se envía como `Authorization: Bearer`.
