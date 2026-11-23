"""Valida los datos de eventos de partido y goleadores."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.core.enums import TipoEventoEnum

Comentario = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]


class EventoPartidoCreate(BaseModel):
    """jugador_id es el protagonista (quien anota, recibe la tarjeta o ENTRA en una sustitución).
    jugador_secundario_id es quien asiste en un gol o quien SALE en una sustitución."""

    model_config = ConfigDict(extra="forbid")

    equipo_id: int = Field(gt=0)
    jugador_id: int = Field(gt=0)
    jugador_secundario_id: int | None = Field(default=None, gt=0)
    tipo_evento: TipoEventoEnum
    minuto_ocurrencia: int = Field(ge=0, le=150)
    comentarios: Comentario | None = None

    @model_validator(mode="after")
    def validar_secundario(self) -> "EventoPartidoCreate":
        if self.jugador_secundario_id is not None and self.jugador_secundario_id == self.jugador_id:
            raise ValueError("El jugador secundario debe ser distinto del principal.")
        if self.tipo_evento == TipoEventoEnum.SUSTITUCION and self.jugador_secundario_id is None:
            raise ValueError("Una sustitución exige jugador_secundario_id (el jugador que sale).")
        if self.jugador_secundario_id is not None and self.tipo_evento not in (
            TipoEventoEnum.GOL,
            TipoEventoEnum.SUSTITUCION,
        ):
            raise ValueError("Solo un gol (asistente) o una sustitución (quien sale) llevan jugador secundario.")
        return self


class EventoPartidoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    partido_id: int
    equipo_id: int
    jugador_id: int
    jugador_secundario_id: int | None = None
    tipo_evento: TipoEventoEnum
    minuto_ocurrencia: int
    comentarios: str | None = None


class GoleadorResponse(BaseModel):
    jugador_id: int
    nombre_completo: str
    equipo_id: int
    goles: int
