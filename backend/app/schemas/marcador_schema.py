"""Valida los datos de marcadores que devuelve la API."""

from pydantic import BaseModel, ConfigDict, Field, model_validator


class MarcadorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    partido_id: int
    goles_local: int
    goles_visitante: int
    goles_penales_local: int | None = None
    goles_penales_visitante: int | None = None
    es_resultado_final: bool


class MarcadorUpdate(BaseModel):
    """Resultado que registra el árbitro. Los penales solo aplican en fases de eliminatoria directa."""

    model_config = ConfigDict(extra="forbid")

    goles_local: int = Field(ge=0, le=99)
    goles_visitante: int = Field(ge=0, le=99)
    goles_penales_local: int | None = Field(default=None, ge=0, le=99)
    goles_penales_visitante: int | None = Field(default=None, ge=0, le=99)

    @model_validator(mode="after")
    def penales_completos(self) -> "MarcadorUpdate":
        if (self.goles_penales_local is None) != (self.goles_penales_visitante is None):
            raise ValueError("Los penales se registran para los dos equipos o para ninguno.")
        return self
