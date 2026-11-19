"""Define cómo se guardan las fases (etapas) de un torneo en la base de datos."""

from sqlalchemy import Column, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy import Enum as SQLEnum

from app.core.enums import EstadoFaseEnum, TipoFormatoEnum
from app.database import Base


class FaseModel(Base):
    __tablename__ = "fases"
    # Un torneo no puede tener dos fases con el mismo nombre.
    __table_args__ = (UniqueConstraint("torneo_id", "nombre", name="uq_fase_torneo_nombre"),)

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    torneo_id = Column(Integer, ForeignKey("torneos.id"), nullable=False, index=True)
    nombre = Column(String, nullable=False)
    tipo_formato = Column(SQLEnum(TipoFormatoEnum), nullable=False)
    estado = Column(SQLEnum(EstadoFaseEnum), nullable=False, default=EstadoFaseEnum.PROGRAMADA)
