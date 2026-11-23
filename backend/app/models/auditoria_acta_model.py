"""Registro de las correcciones que el Administrador hace a actas ya cerradas."""

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func

from app.database import Base


class AuditoriaActaModel(Base):
    __tablename__ = "auditoria_actas"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    partido_id = Column(Integer, ForeignKey("partidos.id"), nullable=False, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)  # el administrador que corrigió
    fecha = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    motivo = Column(String, nullable=False)
    datos_anteriores = Column(JSON, nullable=False)
    datos_nuevos = Column(JSON, nullable=False)
