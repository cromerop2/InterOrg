"""Plantilla del equipo; consultar fixtures no requiere cuenta de jugador."""
from sqlalchemy import Column, Integer, String, ForeignKey, Date, Boolean, CheckConstraint
from app.database import Base

class JugadorModel(Base):
    __tablename__ = "jugadores"
    __table_args__ = (CheckConstraint("numero_camiseta IS NULL OR numero_camiseta >= 0", name="ck_jugador_camiseta"),)
    id = Column(Integer, primary_key=True)
    equipo_id = Column(Integer, ForeignKey("equipos.id"), nullable=False, index=True)
    nombre_completo = Column(String, nullable=False)
    identificacion = Column(String, nullable=False, unique=True)
    fecha_nacimiento = Column(Date, nullable=False)
    numero_camiseta = Column(Integer, nullable=True)
    estado_activo = Column(Boolean, nullable=False, default=True)
