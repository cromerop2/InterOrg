"""Vínculo único entre un equipo y cada campeonato en que participa."""
from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from app.database import Base

class InscripcionModel(Base):
    __tablename__ = "inscripciones"
    __table_args__ = (UniqueConstraint("torneo_id", "equipo_id", name="uq_inscripcion_equipo"),)
    id = Column(Integer, primary_key=True)
    torneo_id = Column(Integer, ForeignKey("torneos.id"), nullable=False, index=True)
    equipo_id = Column(Integer, ForeignKey("equipos.id"), nullable=False, index=True)
    grupo_id = Column(Integer, ForeignKey("grupos.id"), nullable=True, index=True)
