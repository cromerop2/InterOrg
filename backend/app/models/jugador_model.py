"""Define cómo se guardan los jugadores de la plantilla de un equipo."""

from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, String

from app.database import Base


class JugadorModel(Base):
    __tablename__ = "jugadores"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    equipo_id = Column(Integer, ForeignKey("equipos.id"), nullable=False, index=True)
    nombre_completo = Column(String, nullable=False)
    # Único por torneo (no global): lo valida JugadorService, porque el torneo se alcanza vía el equipo.
    identificacion = Column(String, nullable=False, index=True)
    fecha_nacimiento = Column(Date, nullable=False)
    numero_camiseta = Column(Integer, nullable=True)
    posicion = Column(String, nullable=True)
    estado_activo = Column(Boolean, nullable=False, default=True)
    sancionado = Column(Boolean, nullable=False, default=False)
    # Partidos de su equipo que aún debe cumplir de suspensión. Cada partido cerrado del equipo descuenta 1
    # y, al llegar a 0, deja de estar sancionado. Con sancionado=True y 0 fechas, el bloqueo no vence solo.
    fechas_suspension = Column(Integer, nullable=False, default=0, server_default="0")
