"""Valida la corrección de actas cerradas y su registro de auditoría."""

from datetime import datetime
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

Motivo = Annotated[str, StringConstraints(strip_whitespace=True, min_length=10, max_length=500)]


class ActaCorreccion(BaseModel):
    """Corrección de un acta cerrada. Se envía el motivo y UNA de estas dos cosas:
    el marcador correcto, o el equipo que gana por W.O. (alineación indebida, apelación...)."""

    model_config = ConfigDict(extra="forbid")

    motivo_auditoria: Motivo
    goles_local: int | None = Field(default=None, ge=0, le=99)
    goles_visitante: int | None = Field(default=None, ge=0, le=99)
    goles_penales_local: int | None = Field(default=None, ge=0, le=99)
    goles_penales_visitante: int | None = Field(default=None, ge=0, le=99)
    walkover_ganador_id: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def una_sola_correccion(self) -> "ActaCorreccion":
        hay_marcador = self.goles_local is not None or self.goles_visitante is not None
        if hay_marcador and (self.goles_local is None or self.goles_visitante is None):
            raise ValueError("Envía los goles de los dos equipos.")
        if hay_marcador == (self.walkover_ganador_id is not None):
            raise ValueError("Envía el marcador correcto o el ganador por W.O., pero no ambos ni ninguno.")
        if (self.goles_penales_local is None) != (self.goles_penales_visitante is None):
            raise ValueError("Los penales se registran para los dos equipos o para ninguno.")
        if self.walkover_ganador_id is not None and self.goles_penales_local is not None:
            raise ValueError("Un W.O. no lleva penales.")
        return self


class AuditoriaActaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    partido_id: int
    usuario_id: int
    fecha: datetime
    motivo: str
    datos_anteriores: dict[str, Any]
    datos_nuevos: dict[str, Any]
