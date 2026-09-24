from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class JugadorBase(BaseModel):
    nombre: str = Field(..., example="Juan Pérez")
    identificacion: str = Field(..., example="123456789")
    fecha_nacimiento: Optional[str] = Field(None, example="2005-05-15")
    numero_camiseta: int = Field(..., example=10)
    posicion: str = Field(..., example="Delantero")

class JugadorCreate(JugadorBase):
    pass

class JugadorResponse(JugadorBase):
    id: int = Field(..., example=1)

    class Config:
        from_attributes = True