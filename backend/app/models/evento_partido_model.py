"""Define cómo se guardan los eventos de un partido (goles, tarjetas, sustituciones...)."""

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy import Enum as SQLEnum

from app.core.enums import TipoEventoEnum
from app.database import Base


class EventoPartidoModel(Base):
    __tablename__ = "eventos_partido"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    partido_id = Column(Integer, ForeignKey("partidos.id"), nullable=False, index=True)
    equipo_id = Column(Integer, ForeignKey("equipos.id"), nullable=False, index=True)
    jugador_id = Column(Integer, ForeignKey("jugadores.id"), nullable=False, index=True)
    # Quien asiste en un gol, o quien sale en una sustitución.
    jugador_secundario_id = Column(Integer, ForeignKey("jugadores.id"), nullable=True)
    tipo_evento = Column(SQLEnum(TipoEventoEnum), nullable=False)
    minuto_ocurrencia = Column(Integer, nullable=False)
    comentarios = Column(String, nullable=True)
