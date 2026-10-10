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
