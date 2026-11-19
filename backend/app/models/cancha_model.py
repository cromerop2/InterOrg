"""Define cómo se guardan las canchas (escenarios deportivos) en la base de datos."""

from sqlalchemy import Boolean, Column, Integer, String

from app.database import Base


class CanchaModel(Base):
    __tablename__ = "canchas"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String, index=True, nullable=False)
    direccion_sede = Column(String, nullable=False)
    tipo_superficie = Column(String, nullable=True)
    # False cuando la cancha entra en remodelación o se pierde el contrato; el historial se conserva.
    estado_activo = Column(Boolean, default=True, nullable=False)
