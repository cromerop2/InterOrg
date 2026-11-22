"""Valida los datos de marcadores que devuelve la API."""

from pydantic import BaseModel, ConfigDict


class MarcadorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    partido_id: int
    goles_local: int
    goles_visitante: int
    goles_penales_local: int | None = None
    goles_penales_visitante: int | None = None
    es_resultado_final: bool
