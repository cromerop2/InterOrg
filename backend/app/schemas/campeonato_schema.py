"""Contratos JSON compartidos por la app móvil y el panel administrativo."""
from datetime import date, datetime, timezone
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator, AwareDatetime, field_validator

Texto = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
Identificador = Annotated[int, Field(gt=0)]


class Entrada(BaseModel):
    """Rechaza campos desconocidos para detectar errores del cliente."""
    model_config = ConfigDict(extra="forbid", from_attributes=True)


class TorneoCreate(Entrada):
    nombre: Texto
    categoria: Texto
    fecha_inicio: date
    fecha_fin: date
    numero_grupos: int = Field(default=2, ge=1, le=32)
    clasifican_por_grupo: int = Field(default=2, ge=1, le=8)

    @model_validator(mode="after")
    def validar_fechas(self):
        if self.fecha_fin < self.fecha_inicio:
            raise ValueError("El fin del campeonato no puede preceder al inicio.")
        total = self.numero_grupos * self.clasifican_por_grupo
        if total < 2 or total & (total - 1):
            raise ValueError("El total de clasificados debe ser una potencia de dos (2, 4, 8...).")
        return self


class TorneoResponse(TorneoCreate):
    id: int
    estado: Literal["Inscripciones", "En_Curso", "Finalizado", "Cancelado"]


class EquipoCreate(Entrada):
    nombre: Texto
    colegio_id: Identificador
    entrenador_id: Identificador
    escudo_url: Texto | None = None


class EquipoResponse(EquipoCreate):
    id: int
    estado_activo: bool


class JugadorCreate(Entrada):
    equipo_id: Identificador
    nombre_completo: Texto
    identificacion: Texto
    fecha_nacimiento: date
    numero_camiseta: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validar_nacimiento(self):
        if self.fecha_nacimiento > date.today():
            raise ValueError("La fecha de nacimiento no puede estar en el futuro.")
        return self


class JugadorResponse(Entrada):
    """Respuesta de plantilla: no publica documento ni fecha de nacimiento."""
    id: int
    equipo_id: int
    nombre_completo: str
    numero_camiseta: int | None
    estado_activo: bool


class InscripcionCreate(Entrada):
    equipo_id: Identificador


class InscripcionResponse(Entrada):
    id: int
    torneo_id: int
    equipo_id: int
    grupo_id: int | None = None


class ProgramacionUpdate(Entrada):
    """La hora debe incluir zona horaria; el servicio la convierte a UTC."""
    fecha_hora: AwareDatetime
    sede: Texto


class ResultadoUpdate(Entrada):
    goles_local: int = Field(ge=0, le=999)
    goles_visitante: int = Field(ge=0, le=999)
    penales_local: int | None = Field(default=None, ge=0, le=999)
    penales_visitante: int | None = Field(default=None, ge=0, le=999)

    @model_validator(mode="after")
    def validar_penales(self):
        if (self.penales_local is None) != (self.penales_visitante is None):
            raise ValueError("Se deben enviar ambos resultados de penales.")
        return self


class PartidoResponse(Entrada):
    id: int
    torneo_id: int
    fase_id: int
    fase: str
    tipo_fase: str
    grupo_id: int | None
    grupo: str | None
    numero: int
    jornada: int
    equipo_local_id: int
    equipo_local: str
    equipo_visitante_id: int
    equipo_visitante: str
    fecha_hora: datetime | None
    sede: str | None
    estado: str
    goles_local: int | None
    goles_visitante: int | None
    penales_local: int | None
    penales_visitante: int | None

    @field_validator("fecha_hora")
    @classmethod
    def mostrar_utc(cls, valor):
        # SQLite pierde el offset; todas las escrituras ya están normalizadas a UTC.
        return valor.replace(tzinfo=timezone.utc) if valor and valor.tzinfo is None else valor


class FilaPosicionResponse(Entrada):
    equipo_id: int
    equipo: str
    posicion: int
    pj: int
    pg: int
    pe: int
    pp: int
    gf: int
    gc: int
    dg: int
    puntos: int


class GrupoResponse(Entrada):
    id: int
    nombre: str
    posiciones: list[FilaPosicionResponse]
    criterio_desempate: str = "Puntos, diferencia de goles, goles a favor, orden de inscripción."


class SeguimientoResponse(Entrada):
    torneo: TorneoResponse
    equipos_inscritos: int
    partidos_generados: int
    partidos_finalizados: int
    partidos_pendientes: int
    fase_actual: str | None
    campeon_id: int | None
    campeon: str | None
    # El fixture eliminatorio se amplía al avanzar; este porcentaje es de los partidos ya generados.
    porcentaje_fixture_completado: float
