"""Valida los datos de torneos que recibe y devuelve la API."""

from datetime import date
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, StringConstraints, model_validator

from app.core.enums import EstadoTorneoEnum

TextoObligatorio = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class TorneoBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    nombre: TextoObligatorio  # Ej.: "Copa Intercolegial 2026"
    categoria: TextoObligatorio  # Ej.: "Sub-17", "Femenino Libre"
    fecha_inicio: date
    fecha_fin: date
    # Configuración libre: límite de jugadores, puntos por victoria, enlace al reglamento...
    reglas: dict[str, Any] | None = None

    @model_validator(mode="after")
    def fechas_en_orden(self) -> "TorneoBase":
        if self.fecha_fin < self.fecha_inicio:
            raise ValueError("fecha_fin no puede ser anterior a fecha_inicio.")
        return self


class TorneoCreate(TorneoBase):
    """El estado inicial siempre es "Inscripciones"; no se envía."""


class TorneoUpdate(BaseModel):
    """PATCH parcial de datos. El estado cambia solo con las acciones /finalizar y /cancelar."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    nombre: TextoObligatorio | None = None
    categoria: TextoObligatorio | None = None
    fecha_inicio: date | None = None
    fecha_fin: date | None = None
    reglas: dict[str, Any] | None = None

    @model_validator(mode="after")
    def validar_campos(self) -> "TorneoUpdate":
        for campo in self.model_fields_set - {"reglas"}:
            if getattr(self, campo) is None:
                raise ValueError(f"El campo {campo} no puede ser nulo.")
        if self.fecha_inicio and self.fecha_fin and self.fecha_fin < self.fecha_inicio:
            raise ValueError("fecha_fin no puede ser anterior a fecha_inicio.")
        return self


class TorneoResponse(TorneoBase):
    id: int
    estado: EstadoTorneoEnum

    model_config = ConfigDict(from_attributes=True)
