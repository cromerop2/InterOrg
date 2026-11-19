"""Valida los datos de usuarios, login y respuestas de la API."""

from datetime import datetime
from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints, field_validator

from app.core.enums import RolEnum

# Elimina espacios de los extremos y rechaza textos vacíos.
TextoObligatorio = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class UsuarioCreateBase(BaseModel):
    """Campos comunes a los tres roles."""

    # extra="forbid": un campo que no corresponde al rol (p. ej. colegio_id en un Arbitro) da error 422.
    model_config = ConfigDict(extra="forbid")

    nombre_completo: TextoObligatorio
    email: EmailStr
    telefono_contacto: TextoObligatorio
    # bcrypt solo admite 72 bytes; el servicio vuelve a comprobarlo por si hay caracteres multibyte.
    password: str = Field(min_length=8, max_length=72)

    @field_validator("email")
    @classmethod
    def correo_en_minusculas(cls, valor: str) -> str:
        # Evita duplicados por mayúsculas (Ana@x.co vs ana@x.co).
        return valor.lower()


class AdministradorCreate(UsuarioCreateBase):
    rol: Literal["Administrador"]
    # Opcional: si no se envía, el modelo usa "Total".
    nivel_acceso: TextoObligatorio | None = None


class EntrenadorCreate(UsuarioCreateBase):
    rol: Literal["Entrenador"]
    colegio_id: int | None = Field(default=None, gt=0)


class ArbitroCreate(UsuarioCreateBase):
    rol: Literal["Arbitro"]
    numero_colegiado: TextoObligatorio | None = None


# El campo "rol" decide qué esquema se aplica al cuerpo del POST.
UsuarioCreate = Annotated[
    Union[AdministradorCreate, EntrenadorCreate, ArbitroCreate],
    Field(discriminator="rol"),
]


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def correo_en_minusculas(cls, valor: str) -> str:
        return valor.lower()


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    rol: RolEnum


class UsuarioEstadoUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    estado_activo: bool


class UsuarioResponse(BaseModel):
    """Nunca incluye password_hash."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre_completo: str
    email: str
    telefono_contacto: str | None = None
    rol: RolEnum
    estado_activo: bool
    fecha_creacion: datetime | None = None
    # Campos propios de cada rol; quedan en None para los demás.
    nivel_acceso: str | None = None
    colegio_id: int | None = None
    numero_colegiado: str | None = None
