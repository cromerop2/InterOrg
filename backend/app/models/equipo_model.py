"""Equipo reutilizable: su participación se guarda en InscripcionModel."""
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from app.database import Base

class EquipoModel(Base):
    __tablename__ = "equipos"
    id = Column(Integer, primary_key=True)
    nombre = Column(String, nullable=False)
    colegio_id = Column(Integer, ForeignKey("colegios.id"), nullable=False, index=True)
    entrenador_id = Column(Integer, ForeignKey("entrenadores.id"), nullable=False, index=True)
    escudo_url = Column(String, nullable=True)
    estado_activo = Column(Boolean, nullable=False, default=True)
