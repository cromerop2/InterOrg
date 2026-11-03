"""Campeonato: datos generales y estado de la competición."""
from sqlalchemy import Column, Integer, String, Date, CheckConstraint
from app.database import Base

class TorneoModel(Base):
    __tablename__ = "torneos"
    __table_args__ = (
        CheckConstraint("fecha_fin >= fecha_inicio", name="ck_torneo_fechas"),
        CheckConstraint("estado IN ('Inscripciones', 'En_Curso', 'Finalizado', 'Cancelado')", name="ck_torneo_estado"),
    )
    id = Column(Integer, primary_key=True)
    nombre = Column(String, nullable=False)
    categoria = Column(String, nullable=False)
    numero_grupos = Column(Integer, nullable=False, default=2)
    clasifican_por_grupo = Column(Integer, nullable=False, default=2)
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date, nullable=False)
    estado = Column(String, nullable=False, default="Inscripciones")
