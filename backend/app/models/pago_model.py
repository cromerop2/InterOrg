"""Define cómo se guardan los pagos de inscripción reportados por los entrenadores."""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.sql import func

from app.core.enums import EstadoPagoEnum
from app.database import Base


class PagoModel(Base):
    __tablename__ = "pagos"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    equipo_id = Column(Integer, ForeignKey("equipos.id"), nullable=False, index=True)
    monto = Column(Numeric(12, 2), nullable=False)
    # Momento en que se reporta el pago; lo fija el servidor.
    fecha = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    metodo_pago = Column(String, nullable=False)
    referencia_transaccion = Column(String, nullable=True, index=True)
    comprobante_url = Column(String, nullable=True)
    estado = Column(SQLEnum(EstadoPagoEnum), nullable=False, default=EstadoPagoEnum.PENDIENTE)
    # Motivo cuando el Administrador rechaza el pago (ej. "Comprobante ilegible").
    observaciones = Column(String, nullable=True)
