# Pruebas

Esta carpeta contiene las pruebas realizadas sobre la solución.

Puede incluir pruebas unitarias, de integración, APIs, funcionales u otras evidencias de validación del proyecto.

## Colegio

Desde `backend`, con el entorno virtual activado:

```powershell
python -m pip install -r requirements-dev.txt
python -m unittest discover -s ../tests -p "test_colegio.py" -v
```

Verificación del 10 de octubre de 2026: **11 pruebas aprobadas**.

- Crear, consultar por ID, listar y actualizar colegios.
- Rechazar nombres duplicados, incluso de colegios inactivos, al crear o actualizar.
- Validar campos obligatorios, textos vacíos, correo, valores nulos e IDs inválidos.
- Conservar campos omitidos y permitir borrar el correo opcional.
- Desactivar, reactivar y filtrar colegios activos.
- Devolver 404 para colegios inexistentes, 409 para duplicados y 422 para entradas inválidas.
- Aplicar la restricción única en la BD y recuperar la sesión después de un conflicto.
- Arrancar Uvicorn, acceder a Swagger y ejecutar las cuatro operaciones por HTTP real.
- Reiniciar el servidor y comprobar que los datos siguen guardados.

## Pruebas de usuarios y seguridad

`python -m unittest discover -s ../tests -p "test_usuario.py" -v` (desde `backend`). Usan SQLite en memoria.

Las pruebas de Cancha, Torneo y Fase (`test_cancha.py`, `test_torneo.py`) usan la base común `base_api.py`,
que siembra un administrador con sesión iniciada. Para correr todo: `python -m unittest discover -s ../tests -p "test_*.py" -v`.

`test_equipo.py`, `test_jugador.py` y `test_pago.py` usan `BaseInscripcionTest` (en `base_api.py`), que agrega un colegio,
un torneo Sub-17 con reglas pequeñas y dos entrenadores con sesión. Toda la suite tarda un poco porque cada prueba encripta contraseñas.

`test_partido.py`, `test_alineacion.py` y `test_tabla.py` usan `BasePartidoTest` (en `base_api.py`): un torneo En_Curso con 6 equipos Habilitados (A a F),
dos fases, dos canchas y dos árbitros. Con `INICIALIZAR_GRUPOS = False` la prueba arma sus propios grupos.

`test_juego.py`, `test_eventos.py` y `test_clasificacion.py` también usan `BasePartidoTest`, con ayudantes para jugar partidos completos
(`preparar_partido`, `terminar_partido`, `jugar_partido`) y reglas de prueba de 2 titulares, 1 suplente y 1 sustitución.
