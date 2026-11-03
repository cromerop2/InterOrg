"""Partidos del fixture y resultados; solo los finalizados suman en la tabla."""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, ForeignKeyConstraint, CheckConstraint, UniqueConstraint
from app.database import Base

class PartidoModel(Base):
    __tablename__ = "partidos"
    __table_args__ = (
        ForeignKeyConstraint(["torneo_id", "equipo_local_id"], ["inscripciones.torneo_id", "inscripciones.equipo_id"]),
        ForeignKeyConstraint(["torneo_id", "equipo_visitante_id"], ["inscripciones.torneo_id", "inscripciones.equipo_id"]),
        UniqueConstraint("fase_id", "numero", name="uq_partido_numero"),
        CheckConstraint("equipo_local_id <> equipo_visitante_id", name="ck_partido_equipos"),
        CheckConstraint("estado IN ('Programado', 'Finalizado')", name="ck_partido_estado"),
        CheckConstraint("goles_local IS NULL OR goles_local >= 0", name="ck_partido_gl"),
        CheckConstraint("goles_visitante IS NULL OR goles_visitante >= 0", name="ck_partido_gv"),
        CheckConstraint("penales_local IS NULL OR penales_local >= 0", name="ck_partido_pl"),
        CheckConstraint("penales_visitante IS NULL OR penales_visitante >= 0", name="ck_partido_pv"),
        CheckConstraint("estado <> 'Finalizado' OR (goles_local IS NOT NULL AND goles_visitante IS NOT NULL)", name="ck_partido_resultado"),
    )
    id = Column(Integer, primary_key=True)
    torneo_id = Column(Integer, ForeignKey("torneos.id"), nullable=False, index=True)
    fase_id = Column(Integer, ForeignKey("fases.id"), nullable=False, index=True)
    grupo_id = Column(Integer, ForeignKey("grupos.id"), nullable=True)
    numero = Column(Integer, nullable=False)
    jornada = Column(Integer, nullable=False)
    equipo_local_id = Column(Integer, ForeignKey("equipos.id"), nullable=False)
    equipo_visitante_id = Column(Integer, ForeignKey("equipos.id"), nullable=False)
    # Se programa después del sorteo; las horas se almacenan normalizadas a UTC.
    fecha_hora = Column(DateTime(timezone=True), nullable=True)
    sede = Column(String, nullable=True)
    estado = Column(String, nullable=False, default="Programado")
    goles_local = Column(Integer, nullable=True)
    goles_visitante = Column(Integer, nullable=True)
    penales_local = Column(Integer, nullable=True)
    penales_visitante = Column(Integer, nullable=True)
