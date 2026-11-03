from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from app.core.enums import RolEnum

# 1. Esquema Base de Usuario
class UsuarioBase(BaseModel):
    nombre_completo: str = Field(..., min_length=1, example="Carlos Romero")
    email: EmailStr = Field(..., example="carlos.romero@universidad.edu.co")
    telefono_contacto: str = Field(..., min_length=1, example="3001234567")
    rol: RolEnum = Field(..., example=RolEnum.ADMINISTRADOR)

class UsuarioCreate(UsuarioBase):
    password: str = Field(..., min_length=8, max_length=1024, example="segura12345")
    # El administrador puede proporcionar los atributos específicos de cada rol.
    nivel_acceso: str = Field(default="Total", min_length=1)
    numero_colegiado: str | None = Field(default=None, min_length=1)

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)

# 2. Esquema específico para Administrador
class AdministradorCreate(UsuarioCreate):
    nivel_acceso: str = Field(..., example="Total")

# 3. Esquema específico para Entrenador
class EntrenadorCreate(UsuarioCreate):
    colegio_id: Optional[int] = Field(None, example=1)

# 4. Esquema específico para Árbitro
class ArbitroCreate(UsuarioCreate):
    numero_colegiado: str = Field(..., example="COL-ARB-042")

# 5. Respuesta Genérica de Usuario
class UsuarioResponse(UsuarioBase):
    id: int = Field(..., example=1)
    estado_activo: bool = Field(..., example=True)
    fecha_creacion: datetime

    model_config = ConfigDict(from_attributes=True)
