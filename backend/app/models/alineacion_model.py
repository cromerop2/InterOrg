"""Define cómo se guardan las alineaciones: qué jugadores de cada equipo van a un partido."""

from sqlalchemy import Boolean, Column, ForeignKey, Integer, UniqueConstraint

from app.database import Base


class AlineacionModel(Base):
    __tablename__ = "alineaciones"
    # Un jugador aparece una sola vez en la planilla de un partido.
    __table_args__ = (UniqueConstraint("partido_id", "jugador_id", name="uq_alineacion_partido_jugador"),)

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    partido_id = Column(Integer, ForeignKey("partidos.id"), nullable=False, index=True)
    equipo_id = Column(Integer, ForeignKey("equipos.id"), nullable=False, index=True)
    jugador_id = Column(Integer, ForeignKey("jugadores.id"), nullable=False, index=True)
    es_titular = Column(Boolean, nullable=False)
    # Permite usar otro número solo en este partido (camisetas prestadas).
    numero_camiseta = Column(Integer, nullable=True)
