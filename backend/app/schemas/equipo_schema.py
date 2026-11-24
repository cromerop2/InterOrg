"""Valida los datos de equipos que recibe y devuelve la API."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.core.enums import EstadoInscripcionEnum

TextoObligatorio = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class EquipoCreate(BaseModel):
    """El entrenador dueño sale del token de sesión; no se envía."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    colegio_id: int = Field(gt=0)
    torneo_id: int = Field(gt=0)
    nombre: TextoObligatorio  # Ej.: "Selección Prejuvenil"
    escudo_url: TextoObligatorio | None = None


class EquipoAuditoria(BaseModel):
    """Pago que el Administrador revisa para habilitar el equipo."""

    model_config = ConfigDict(extra="forbid")

    id_pago: int = Field(gt=0)


class EquipoPublicoResponse(BaseModel):
    """Lo mínimo de un equipo habilitado que ve cualquier visitante (tablas, calendario)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    colegio_id: int
    nombre: str
    escudo_url: str | None = None


class EquipoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    colegio_id: int
    entrenador_id: int
    torneo_id: int
    nombre: str
    escudo_url: str | None = None
    estado_inscripcion: EstadoInscripcionEnum
    plantilla_bloqueada: bool
