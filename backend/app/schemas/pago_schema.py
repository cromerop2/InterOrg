"""Valida los datos de pagos que recibe y devuelve la API."""

from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.core.enums import EstadoPagoEnum

TextoObligatorio = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class PagoCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    monto: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    metodo_pago: TextoObligatorio  # Ej.: "Transferencia", "Efectivo", "Consignación"
    referencia_transaccion: TextoObligatorio | None = None  # número de comprobante del banco
    comprobante_url: TextoObligatorio | None = None  # foto o PDF del recibo


class PagoValidacion(BaseModel):
    """Decisión del Administrador sobre un pago pendiente."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    aprobado: bool
    observaciones: TextoObligatorio | None = None

    @model_validator(mode="after")
    def rechazo_con_motivo(self) -> "PagoValidacion":
        if not self.aprobado and not self.observaciones:
            raise ValueError("Al rechazar un pago debes indicar las observaciones.")
        return self


class PagoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    equipo_id: int
    monto: Decimal
    fecha: datetime
    metodo_pago: str
    referencia_transaccion: str | None = None
    comprobante_url: str | None = None
    estado: EstadoPagoEnum
    observaciones: str | None = None
