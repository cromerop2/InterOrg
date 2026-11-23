"""Valida los datos de partidos que recibe y devuelve la API."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, NaiveDatetime, model_validator

from app.core.enums import EstadoPartidoEnum

# NaiveDatetime: se envía la hora local de la sede sin zona horaria (ej. "2026-12-05T10:00:00").
# Un valor con zona ("...Z" o "+00:00") se rechaza para no desplazar horarios sin darse cuenta.


class PartidoCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fase_id: int = Field(gt=0)
    equipo_local_id: int = Field(gt=0)
    equipo_visitante_id: int = Field(gt=0)
    cancha_id: int = Field(gt=0)
    fecha_hora: NaiveDatetime
    arbitro_id: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def equipos_distintos(self) -> "PartidoCreate":
        if self.equipo_local_id == self.equipo_visitante_id:
            raise ValueError("Un equipo no puede jugar contra sí mismo.")
        return self


class PartidoReprogramacion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fecha_hora: NaiveDatetime
    cancha_id: int | None = Field(default=None, gt=0)  # si se omite, se conserva la cancha


class PartidoArbitro(BaseModel):
    model_config = ConfigDict(extra="forbid")

    arbitro_id: int = Field(gt=0)


class PartidoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fase_id: int
    equipo_local_id: int
    equipo_visitante_id: int
    cancha_id: int
    arbitro_id: int | None = None
    fecha_hora: datetime
    estado: EstadoPartidoEnum


class PartidoWalkover(BaseModel):
    """Equipo que se presentó y gana por W.O."""

    model_config = ConfigDict(extra="forbid")

    equipo_ganador_id: int = Field(gt=0)
