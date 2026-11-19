"""Define cómo se guardan los torneos en la base de datos."""

from sqlalchemy import JSON, Column, Date, Integer, String
from sqlalchemy import Enum as SQLEnum

from app.core.enums import EstadoTorneoEnum
from app.database import Base


class TorneoModel(Base):
    __tablename__ = "torneos"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String, index=True, nullable=False)
    categoria = Column(String, nullable=False)
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date, nullable=False)
    estado = Column(SQLEnum(EstadoTorneoEnum), nullable=False, default=EstadoTorneoEnum.INSCRIPCIONES)
    # Configuraciones libres: límite de jugadores, puntos por victoria, enlace al reglamento...
    reglas = Column(JSON, nullable=True)
