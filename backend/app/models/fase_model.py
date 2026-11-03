"""Etapas generadas: grupos y sucesivas rondas de eliminación directa."""
from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from app.database import Base

class FaseModel(Base):
    __tablename__ = "fases"
    __table_args__ = (UniqueConstraint("torneo_id", "orden", name="uq_fase_orden"),)
    id = Column(Integer, primary_key=True)
    torneo_id = Column(Integer, ForeignKey("torneos.id"), nullable=False, index=True)
    nombre = Column(String, nullable=False)
    tipo = Column(String, nullable=False)
    orden = Column(Integer, nullable=False)
