"""Valida los datos de canchas que recibe y devuelve la API."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints, model_validator

TextoObligatorio = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class CanchaBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    nombre: TextoObligatorio
    direccion_sede: TextoObligatorio
    tipo_superficie: TextoObligatorio | None = None  # Ej.: "Sintética", "Grama Natural"
    estado_activo: bool = True


class CanchaCreate(CanchaBase):
    pass


class CanchaUpdate(BaseModel):
    """PATCH parcial de datos. El estado se cambia aparte, en /canchas/{id}/estado."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    nombre: TextoObligatorio | None = None
    direccion_sede: TextoObligatorio | None = None
    tipo_superficie: TextoObligatorio | None = None

    @model_validator(mode="after")
    def sin_nulos_en_obligatorios(self) -> "CanchaUpdate":
        # Omitir un campo lo conserva; solo tipo_superficie admite borrarse con null.
        for campo in self.model_fields_set - {"tipo_superficie"}:
            if getattr(self, campo) is None:
                raise ValueError(f"El campo {campo} no puede ser nulo.")
        return self


class CanchaEstadoUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    estado_activo: bool


class CanchaResponse(CanchaBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
