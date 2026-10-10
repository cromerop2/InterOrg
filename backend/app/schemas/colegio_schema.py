"""Valida los datos que recibe la API y define el formato de sus respuestas."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, StringConstraints, model_validator


# Tipo reutilizable: elimina espacios de los extremos y rechaza textos vacíos.
TextoObligatorio = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class ColegioBase(BaseModel):
    """Campos comunes a la creación y a la respuesta de un colegio."""

    # Rechaza campos desconocidos para detectar errores en el JSON recibido.
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    nombre: TextoObligatorio
    direccion: TextoObligatorio
    representante_legal: TextoObligatorio
    telefono_contacto: TextoObligatorio
    # EmailStr comprueba el formato del correo; None permite omitirlo.
    email_institucional: EmailStr | None = None
    estado_activo: bool = True


class ColegioCreate(ColegioBase):
    """Cuerpo del POST: hereda los campos de ColegioBase; el ID lo genera la BD."""

    pass


class ColegioUpdate(BaseModel):
    """Cuerpo del PATCH: permite enviar solo los campos que se quieren cambiar."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    nombre: TextoObligatorio | None = None
    direccion: TextoObligatorio | None = None
    representante_legal: TextoObligatorio | None = None
    telefono_contacto: TextoObligatorio | None = None
    email_institucional: EmailStr | None = None
    estado_activo: bool | None = None

    @model_validator(mode="after")
    def validar_campos_enviados(self) -> "ColegioUpdate":
        """Rechaza null explícito en los campos que la BD exige completar."""
        # Omitir un campo conserva su valor; solo el correo admite borrar su valor.
        # model_fields_set contiene los nombres presentes en el JSON recibido.
        for campo in self.model_fields_set - {"email_institucional"}:
            if getattr(self, campo) is None:
                raise ValueError(f"El campo {campo} no puede ser nulo.")
        return self


class ColegioResponse(ColegioBase):
    """Datos que devuelve la API, incluido el ID asignado al colegio."""

    id: int

    # Permite construir la respuesta leyendo atributos de un ColegioModel.
    model_config = ConfigDict(from_attributes=True)
