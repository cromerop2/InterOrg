"""Define cómo se guardan los grupos (tablas de posiciones) de una fase."""

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, UniqueConstraint

from app.database import Base


class TablaPosicionesModel(Base):
    __tablename__ = "tablas_posiciones"
    __table_args__ = (UniqueConstraint("fase_id", "nombre_grupo", name="uq_tabla_fase_grupo"),)

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    fase_id = Column(Integer, ForeignKey("fases.id"), nullable=False, index=True)
    nombre_grupo = Column(String, nullable=False)  # Ej.: "Grupo A", "Tabla General"
    # True cuando se jugaron todos los partidos y las posiciones son definitivas.
    estado_cierre = Column(Boolean, nullable=False, default=False)
