"""Opciones para generar la programación automática de una fase."""

from datetime import date, time

from pydantic import BaseModel, ConfigDict, Field


class FixtureConfiguracion(BaseModel):
    """Todo es opcional: sin opciones se usan las fechas del torneo, todas las canchas activas y los horarios por defecto."""

    model_config = ConfigDict(extra="forbid")

    fecha_inicio: date | None = None  # primer día disponible (por defecto, el inicio del torneo)
    horas: list[time] | None = Field(default=None, min_length=1, max_length=12)  # ej. ["09:00", "11:00"]
    canchas: list[int] | None = Field(default=None, min_length=1, max_length=20)  # ids de canchas a usar
    asignar_arbitros: bool = False  # asigna un árbitro libre a cada partido, si hay disponibles
