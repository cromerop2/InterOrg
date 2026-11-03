"""Grupos que contienen las inscripciones de la primera fase."""
from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from app.database import Base

class GrupoModel(Base):
    __tablename__ = "grupos"
    __table_args__ = (UniqueConstraint("fase_id", "nombre", name="uq_grupo_nombre"),)
    id = Column(Integer, primary_key=True)
    fase_id = Column(Integer, ForeignKey("fases.id"), nullable=False, index=True)
    nombre = Column(String, nullable=False)
