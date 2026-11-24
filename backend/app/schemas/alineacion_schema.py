"""Valida los datos de alineaciones que recibe y devuelve la API."""

from pydantic import BaseModel, ConfigDict, Field


class JugadorConvocado(BaseModel):
    model_config = ConfigDict(extra="forbid")

    jugador_id: int = Field(gt=0)
    es_titular: bool
    numero_camiseta: int | None = Field(default=None, ge=0, le=99)  # solo para este partido


class AlineacionEnvio(BaseModel):
    """Planilla completa de un equipo para un partido (titulares y suplentes)."""

    model_config = ConfigDict(extra="forbid")

    jugadores: list[JugadorConvocado] = Field(min_length=1, max_length=40)


class AlineacionDetalleResponse(BaseModel):
    """La alineación con los datos del jugador, para la planilla del árbitro."""

    id: int
    partido_id: int
    equipo_id: int
    jugador_id: int
    es_titular: bool
    numero_camiseta: int | None = None  # el de este partido, o el habitual del jugador
    nombre_completo: str
    posicion: str | None = None


class AlineacionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    partido_id: int
    equipo_id: int
    jugador_id: int
    es_titular: bool
    numero_camiseta: int | None = None
