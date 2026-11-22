"""Define cómo se guarda el marcador de cada partido (relación 1 a 1)."""

from sqlalchemy import Boolean, Column, ForeignKey, Integer

from app.database import Base


class MarcadorModel(Base):
    __tablename__ = "marcadores"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    partido_id = Column(Integer, ForeignKey("partidos.id"), nullable=False, unique=True)
    goles_local = Column(Integer, nullable=False, default=0)
    goles_visitante = Column(Integer, nullable=False, default=0)
    # Solo se usan en eliminatorias que terminan empatadas.
    goles_penales_local = Column(Integer, nullable=True)
    goles_penales_visitante = Column(Integer, nullable=True)
    # True cuando se cierra el acta: el resultado ya no se edita.
    es_resultado_final = Column(Boolean, nullable=False, default=False)
