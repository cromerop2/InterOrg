"""Define cómo se guardan las estadísticas de un equipo dentro de un grupo."""

from sqlalchemy import Column, ForeignKey, Integer, UniqueConstraint

from app.database import Base


class FilaPosicionModel(Base):
    __tablename__ = "filas_posicion"
    __table_args__ = (UniqueConstraint("tabla_id", "equipo_id", name="uq_fila_tabla_equipo"),)

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    tabla_id = Column(Integer, ForeignKey("tablas_posiciones.id"), nullable=False, index=True)
    equipo_id = Column(Integer, ForeignKey("equipos.id"), nullable=False, index=True)
    partidos_jugados = Column(Integer, nullable=False, default=0)
    partidos_ganados = Column(Integer, nullable=False, default=0)
    partidos_empatados = Column(Integer, nullable=False, default=0)
    partidos_perdidos = Column(Integer, nullable=False, default=0)
    goles_a_favor = Column(Integer, nullable=False, default=0)
    goles_en_contra = Column(Integer, nullable=False, default=0)
    diferencia_goles = Column(Integer, nullable=False, default=0)
    puntos = Column(Integer, nullable=False, default=0)
