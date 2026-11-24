# Base de datos

Esta carpeta contiene los archivos relacionados con la base de datos de la solución.

## Entregables

- Script SQL / NoSQL de creación de la base de datos.
- Tablas, relaciones, claves y restricciones necesarias.
- Scripts adicionales requeridos para ejecutar la solución.

El archivo `.sql` o la colección respectiva (por ejemplo .json) debe permitir reconstruir el esquema de la base de datos.

## Crear la base de datos

`schema.sql` crea los tipos ENUM, las 18 tablas, sus claves, restricciones e índices (PostgreSQL). Sobre una base vacía:

```bash
psql "$DATABASE_URL_PSQL" -v ON_ERROR_STOP=1 -f database/schema.sql
```

Luego crea el primer administrador con `python backend/scripts/crear_admin.py`.
Si cambias un modelo, regenera el archivo con `python database/generar_schema.py` (desde `backend`); `tests/test_esquema_sql.py` falla si queda desactualizado.
Las bases creadas antes de las fases 1 y 5 necesitan además `migraciones/001_*.sql` y `migraciones/002_*.sql`.
