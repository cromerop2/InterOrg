-- Migración para bases de datos creadas ANTES de la Fase 1 (create_all no modifica tablas existentes).
-- Si tu base está vacía o la recreas desde cero, no necesitas ejecutar esto.

-- 1. El entrenador puede vincularse a un colegio.
ALTER TABLE entrenadores ADD COLUMN IF NOT EXISTS colegio_id INTEGER REFERENCES colegios(id);

-- 2. El número de colegiado del árbitro es opcional.
ALTER TABLE arbitros ALTER COLUMN numero_colegiado DROP NOT NULL;

-- 3. Los usuarios creados antes de la Fase 1 tienen la contraseña en TEXTO PLANO y no podrán iniciar sesión.
--    Si son solo datos de prueba, bórralos (descomenta) y crea el primer administrador con scripts/crear_admin.py:
-- DELETE FROM administradores;
-- DELETE FROM entrenadores;
-- DELETE FROM arbitros;
-- DELETE FROM usuarios;
