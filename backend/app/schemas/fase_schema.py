"""Valida los datos de fases que recibe y devuelve la API."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.core.enums import EstadoFaseEnum, TipoFormatoEnum

TextoObligatorio = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class FaseCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    nombre: TextoObligatorio  # Ej.: "Fase de Grupos", "Octavos de Final"
    tipo_formato: TipoFormatoEnum


class ConfiguracionFases(BaseModel):
    """Lista ordenada de fases para crear de una vez (la primera se juega primero)."""

    model_config = ConfigDict(extra="forbid")

    fases: list[FaseCreate] = Field(min_length=1, max_length=10)

    @model_validator(mode="after")
    def nombres_distintos(self) -> "ConfiguracionFases":
        nombres = [fase.nombre for fase in self.fases]
        if len(nombres) != len(set(nombres)):
            raise ValueError("Los nombres de las fases no pueden repetirse.")
        return self


class FaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    torneo_id: int
    nombre: str
    tipo_formato: TipoFormatoEnum
    estado: EstadoFaseEnum
