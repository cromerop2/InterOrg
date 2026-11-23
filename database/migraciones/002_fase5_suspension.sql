-- Migración para bases de datos creadas ANTES de la Fase 5 (create_all no modifica tablas existentes).
-- La tabla nueva auditoria_actas se crea sola al arrancar el servidor; solo falta esta columna.

-- Fechas de suspensión pendientes de cada jugador (cada partido de su equipo descuenta una).
ALTER TABLE jugadores ADD COLUMN IF NOT EXISTS fechas_suspension INTEGER NOT NULL DEFAULT 0;
