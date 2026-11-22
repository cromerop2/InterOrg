"""Define cómo se guardan los equipos inscritos en un torneo."""

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy import Enum as SQLEnum

from app.core.enums import EstadoInscripcionEnum
from app.database import Base


class EquipoModel(Base):
    __tablename__ = "equipos"
    # Dentro de un torneo no puede haber dos equipos con el mismo nombre.
    __table_args__ = (UniqueConstraint("torneo_id", "nombre", name="uq_equipo_torneo_nombre"),)

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    colegio_id = Column(Integer, ForeignKey("colegios.id"), nullable=False, index=True)
    entrenador_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
    torneo_id = Column(Integer, ForeignKey("torneos.id"), nullable=False, index=True)
    nombre = Column(String, nullable=False)
    escudo_url = Column(String, nullable=True)
    estado_inscripcion = Column(
        SQLEnum(EstadoInscripcionEnum), nullable=False, default=EstadoInscripcionEnum.PREINSCRITO
    )
    # True cuando el torneo inicia: ya no se agregan ni se dan de baja jugadores.
    plantilla_bloqueada = Column(Boolean, nullable=False, default=False)
