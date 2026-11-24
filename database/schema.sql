-- Generado desde los modelos con database/generar_schema.py. No editar a mano.


CREATE TYPE estadofaseenum AS ENUM ('PROGRAMADA', 'EN_JUEGO', 'FINALIZADA');

CREATE TYPE estadoinscripcionenum AS ENUM ('PREINSCRITO', 'PAGO_PENDIENTE', 'HABILITADO', 'DESCALIFICADO');

CREATE TYPE estadopagoenum AS ENUM ('PENDIENTE', 'APROBADO', 'RECHAZADO');

CREATE TYPE estadopartidoenum AS ENUM ('PROGRAMADO', 'EN_JUEGO', 'FINALIZADO', 'SUSPENDIDO', 'W_O');

CREATE TYPE estadotorneoenum AS ENUM ('INSCRIPCIONES', 'EN_CURSO', 'FINALIZADO', 'CANCELADO');

CREATE TYPE rolenum AS ENUM ('ADMINISTRADOR', 'ENTRENADOR', 'ARBITRO');

CREATE TYPE tipoeventoenum AS ENUM ('GOL', 'ASISTENCIA', 'TARJETA_AMARILLA', 'TARJETA_ROJA', 'SUSTITUCION', 'AUTOGOL');

CREATE TYPE tipoformatoenum AS ENUM ('GRUPOS', 'ELIMINATORIA_DIRECTA');

CREATE TABLE canchas (
	id SERIAL NOT NULL, 
	nombre VARCHAR NOT NULL, 
	direccion_sede VARCHAR NOT NULL, 
	tipo_superficie VARCHAR, 
	estado_activo BOOLEAN NOT NULL, 
	PRIMARY KEY (id)
);

CREATE INDEX ix_canchas_id ON canchas (id);

CREATE INDEX ix_canchas_nombre ON canchas (nombre);

CREATE TABLE colegios (
	id SERIAL NOT NULL, 
	nombre VARCHAR NOT NULL, 
	direccion VARCHAR NOT NULL, 
	representante_legal VARCHAR NOT NULL, 
	telefono_contacto VARCHAR NOT NULL, 
	email_institucional VARCHAR, 
	estado_activo BOOLEAN NOT NULL, 
	PRIMARY KEY (id)
);

CREATE INDEX ix_colegios_id ON colegios (id);

CREATE UNIQUE INDEX ix_colegios_nombre ON colegios (nombre);

CREATE TABLE torneos (
	id SERIAL NOT NULL, 
	nombre VARCHAR NOT NULL, 
	categoria VARCHAR NOT NULL, 
	fecha_inicio DATE NOT NULL, 
	fecha_fin DATE NOT NULL, 
	estado estadotorneoenum NOT NULL, 
	reglas JSON, 
	PRIMARY KEY (id)
);

CREATE INDEX ix_torneos_id ON torneos (id);

CREATE INDEX ix_torneos_nombre ON torneos (nombre);

CREATE TABLE usuarios (
	id SERIAL NOT NULL, 
	nombre_completo VARCHAR NOT NULL, 
	email VARCHAR NOT NULL, 
	telefono_contacto VARCHAR NOT NULL, 
	password_hash VARCHAR NOT NULL, 
	rol rolenum NOT NULL, 
	estado_activo BOOLEAN, 
	fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT now(), 
	PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_usuarios_email ON usuarios (email);

CREATE INDEX ix_usuarios_id ON usuarios (id);

CREATE TABLE administradores (
	id INTEGER NOT NULL, 
	nivel_acceso VARCHAR NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(id) REFERENCES usuarios (id)
);

CREATE TABLE arbitros (
	id INTEGER NOT NULL, 
	numero_colegiado VARCHAR, 
	PRIMARY KEY (id), 
	FOREIGN KEY(id) REFERENCES usuarios (id), 
	UNIQUE (numero_colegiado)
);

CREATE TABLE entrenadores (
	id INTEGER NOT NULL, 
	colegio_id INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY(id) REFERENCES usuarios (id), 
	FOREIGN KEY(colegio_id) REFERENCES colegios (id)
);

CREATE TABLE equipos (
	id SERIAL NOT NULL, 
	colegio_id INTEGER NOT NULL, 
	entrenador_id INTEGER NOT NULL, 
	torneo_id INTEGER NOT NULL, 
	nombre VARCHAR NOT NULL, 
	escudo_url VARCHAR, 
	estado_inscripcion estadoinscripcionenum NOT NULL, 
	plantilla_bloqueada BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_equipo_torneo_nombre UNIQUE (torneo_id, nombre), 
	FOREIGN KEY(colegio_id) REFERENCES colegios (id), 
	FOREIGN KEY(entrenador_id) REFERENCES usuarios (id), 
	FOREIGN KEY(torneo_id) REFERENCES torneos (id)
);

CREATE INDEX ix_equipos_colegio_id ON equipos (colegio_id);

CREATE INDEX ix_equipos_entrenador_id ON equipos (entrenador_id);

CREATE INDEX ix_equipos_id ON equipos (id);

CREATE INDEX ix_equipos_torneo_id ON equipos (torneo_id);

CREATE TABLE fases (
	id SERIAL NOT NULL, 
	torneo_id INTEGER NOT NULL, 
	nombre VARCHAR NOT NULL, 
	tipo_formato tipoformatoenum NOT NULL, 
	estado estadofaseenum NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_fase_torneo_nombre UNIQUE (torneo_id, nombre), 
	FOREIGN KEY(torneo_id) REFERENCES torneos (id)
);

CREATE INDEX ix_fases_id ON fases (id);

CREATE INDEX ix_fases_torneo_id ON fases (torneo_id);

CREATE TABLE jugadores (
	id SERIAL NOT NULL, 
	equipo_id INTEGER NOT NULL, 
	nombre_completo VARCHAR NOT NULL, 
	identificacion VARCHAR NOT NULL, 
	fecha_nacimiento DATE NOT NULL, 
	numero_camiseta INTEGER, 
	posicion VARCHAR, 
	estado_activo BOOLEAN NOT NULL, 
	sancionado BOOLEAN NOT NULL, 
	fechas_suspension INTEGER DEFAULT '0' NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(equipo_id) REFERENCES equipos (id)
);

CREATE INDEX ix_jugadores_equipo_id ON jugadores (equipo_id);

CREATE INDEX ix_jugadores_id ON jugadores (id);

CREATE INDEX ix_jugadores_identificacion ON jugadores (identificacion);

CREATE TABLE pagos (
	id SERIAL NOT NULL, 
	equipo_id INTEGER NOT NULL, 
	monto NUMERIC(12, 2) NOT NULL, 
	fecha TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	metodo_pago VARCHAR NOT NULL, 
	referencia_transaccion VARCHAR, 
	comprobante_url VARCHAR, 
	estado estadopagoenum NOT NULL, 
	observaciones VARCHAR, 
	PRIMARY KEY (id), 
	FOREIGN KEY(equipo_id) REFERENCES equipos (id)
);

CREATE INDEX ix_pagos_equipo_id ON pagos (equipo_id);

CREATE INDEX ix_pagos_id ON pagos (id);

CREATE INDEX ix_pagos_referencia_transaccion ON pagos (referencia_transaccion);

CREATE TABLE partidos (
	id SERIAL NOT NULL, 
	fase_id INTEGER NOT NULL, 
	equipo_local_id INTEGER NOT NULL, 
	equipo_visitante_id INTEGER NOT NULL, 
	cancha_id INTEGER NOT NULL, 
	arbitro_id INTEGER, 
	fecha_hora TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	estado estadopartidoenum NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_partido_equipos_distintos CHECK (equipo_local_id <> equipo_visitante_id), 
	FOREIGN KEY(fase_id) REFERENCES fases (id), 
	FOREIGN KEY(equipo_local_id) REFERENCES equipos (id), 
	FOREIGN KEY(equipo_visitante_id) REFERENCES equipos (id), 
	FOREIGN KEY(cancha_id) REFERENCES canchas (id), 
	FOREIGN KEY(arbitro_id) REFERENCES usuarios (id)
);

CREATE INDEX ix_partidos_arbitro_id ON partidos (arbitro_id);

CREATE INDEX ix_partidos_cancha_id ON partidos (cancha_id);

CREATE INDEX ix_partidos_equipo_local_id ON partidos (equipo_local_id);

CREATE INDEX ix_partidos_equipo_visitante_id ON partidos (equipo_visitante_id);

CREATE INDEX ix_partidos_fase_id ON partidos (fase_id);

CREATE INDEX ix_partidos_fecha_hora ON partidos (fecha_hora);

CREATE INDEX ix_partidos_id ON partidos (id);

CREATE TABLE tablas_posiciones (
	id SERIAL NOT NULL, 
	fase_id INTEGER NOT NULL, 
	nombre_grupo VARCHAR NOT NULL, 
	estado_cierre BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_tabla_fase_grupo UNIQUE (fase_id, nombre_grupo), 
	FOREIGN KEY(fase_id) REFERENCES fases (id)
);

CREATE INDEX ix_tablas_posiciones_fase_id ON tablas_posiciones (fase_id);

CREATE INDEX ix_tablas_posiciones_id ON tablas_posiciones (id);

CREATE TABLE alineaciones (
	id SERIAL NOT NULL, 
	partido_id INTEGER NOT NULL, 
	equipo_id INTEGER NOT NULL, 
	jugador_id INTEGER NOT NULL, 
	es_titular BOOLEAN NOT NULL, 
	numero_camiseta INTEGER, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_alineacion_partido_jugador UNIQUE (partido_id, jugador_id), 
	FOREIGN KEY(partido_id) REFERENCES partidos (id), 
	FOREIGN KEY(equipo_id) REFERENCES equipos (id), 
	FOREIGN KEY(jugador_id) REFERENCES jugadores (id)
);

CREATE INDEX ix_alineaciones_equipo_id ON alineaciones (equipo_id);

CREATE INDEX ix_alineaciones_id ON alineaciones (id);

CREATE INDEX ix_alineaciones_jugador_id ON alineaciones (jugador_id);

CREATE INDEX ix_alineaciones_partido_id ON alineaciones (partido_id);

CREATE TABLE auditoria_actas (
	id SERIAL NOT NULL, 
	partido_id INTEGER NOT NULL, 
	usuario_id INTEGER NOT NULL, 
	fecha TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	motivo VARCHAR NOT NULL, 
	datos_anteriores JSON NOT NULL, 
	datos_nuevos JSON NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(partido_id) REFERENCES partidos (id), 
	FOREIGN KEY(usuario_id) REFERENCES usuarios (id)
);

CREATE INDEX ix_auditoria_actas_id ON auditoria_actas (id);

CREATE INDEX ix_auditoria_actas_partido_id ON auditoria_actas (partido_id);

CREATE TABLE eventos_partido (
	id SERIAL NOT NULL, 
	partido_id INTEGER NOT NULL, 
	equipo_id INTEGER NOT NULL, 
	jugador_id INTEGER NOT NULL, 
	jugador_secundario_id INTEGER, 
	tipo_evento tipoeventoenum NOT NULL, 
	minuto_ocurrencia INTEGER NOT NULL, 
	comentarios VARCHAR, 
	PRIMARY KEY (id), 
	FOREIGN KEY(partido_id) REFERENCES partidos (id), 
	FOREIGN KEY(equipo_id) REFERENCES equipos (id), 
	FOREIGN KEY(jugador_id) REFERENCES jugadores (id), 
	FOREIGN KEY(jugador_secundario_id) REFERENCES jugadores (id)
);

CREATE INDEX ix_eventos_partido_equipo_id ON eventos_partido (equipo_id);

CREATE INDEX ix_eventos_partido_id ON eventos_partido (id);

CREATE INDEX ix_eventos_partido_jugador_id ON eventos_partido (jugador_id);

CREATE INDEX ix_eventos_partido_partido_id ON eventos_partido (partido_id);

CREATE TABLE filas_posicion (
	id SERIAL NOT NULL, 
	tabla_id INTEGER NOT NULL, 
	equipo_id INTEGER NOT NULL, 
	partidos_jugados INTEGER NOT NULL, 
	partidos_ganados INTEGER NOT NULL, 
	partidos_empatados INTEGER NOT NULL, 
	partidos_perdidos INTEGER NOT NULL, 
	goles_a_favor INTEGER NOT NULL, 
	goles_en_contra INTEGER NOT NULL, 
	diferencia_goles INTEGER NOT NULL, 
	puntos INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_fila_tabla_equipo UNIQUE (tabla_id, equipo_id), 
	FOREIGN KEY(tabla_id) REFERENCES tablas_posiciones (id), 
	FOREIGN KEY(equipo_id) REFERENCES equipos (id)
);

CREATE INDEX ix_filas_posicion_equipo_id ON filas_posicion (equipo_id);

CREATE INDEX ix_filas_posicion_id ON filas_posicion (id);

CREATE INDEX ix_filas_posicion_tabla_id ON filas_posicion (tabla_id);

CREATE TABLE marcadores (
	id SERIAL NOT NULL, 
	partido_id INTEGER NOT NULL, 
	goles_local INTEGER NOT NULL, 
	goles_visitante INTEGER NOT NULL, 
	goles_penales_local INTEGER, 
	goles_penales_visitante INTEGER, 
	es_resultado_final BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (partido_id), 
	FOREIGN KEY(partido_id) REFERENCES partidos (id)
);

CREATE INDEX ix_marcadores_id ON marcadores (id);
