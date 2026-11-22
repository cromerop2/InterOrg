"""Define cómo se guardan los partidos (cruces programados) en la base de datos."""

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer
from sqlalchemy import Enum as SQLEnum

from app.core.enums import EstadoPartidoEnum
from app.database import Base


class PartidoModel(Base):
    __tablename__ = "partidos"
    __table_args__ = (
        CheckConstraint("equipo_local_id <> equipo_visitante_id", name="ck_partido_equipos_distintos"),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    fase_id = Column(Integer, ForeignKey("fases.id"), nullable=False, index=True)
    equipo_local_id = Column(Integer, ForeignKey("equipos.id"), nullable=False, index=True)
    equipo_visitante_id = Column(Integer, ForeignKey("equipos.id"), nullable=False, index=True)
    cancha_id = Column(Integer, ForeignKey("canchas.id"), nullable=False, index=True)
    # Opcional al crear el partido, obligatorio antes de iniciarlo.
    arbitro_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True, index=True)
    # Hora local de la sede, sin zona horaria.
    fecha_hora = Column(DateTime, nullable=False, index=True)
    estado = Column(SQLEnum(EstadoPartidoEnum), nullable=False, default=EstadoPartidoEnum.PROGRAMADO)
