"""Valida los datos de jugadores que recibe y devuelve la API."""

from datetime import date
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

TextoObligatorio = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class JugadorCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    nombre_completo: TextoObligatorio
    identificacion: TextoObligatorio  # documento de identidad
    fecha_nacimiento: date
    numero_camiseta: int | None = Field(default=None, ge=0, le=99)
    posicion: TextoObligatorio | None = None  # Ej.: "Portero", "Defensa"

    @field_validator("fecha_nacimiento")
    @classmethod
    def fecha_razonable(cls, valor: date) -> date:
        if valor > date.today() or valor.year < 1900:
            raise ValueError("fecha_nacimiento no es válida.")
        return valor


class JugadorSancionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sancionado: bool


class JugadorSancionFechas(BaseModel):
    """Sanción disciplinaria por un número de fechas (partidos de su equipo)."""

    model_config = ConfigDict(extra="forbid")

    fechas_suspension: int = Field(ge=1, le=20)


class JugadorTransferencia(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nuevo_equipo_id: int = Field(gt=0)


class JugadorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    equipo_id: int
    nombre_completo: str
    identificacion: str
    fecha_nacimiento: date
    numero_camiseta: int | None = None
    posicion: str | None = None
    estado_activo: bool
    sancionado: bool
    fechas_suspension: int = 0
