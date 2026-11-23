"""Acceso a la BD para eventos de partido."""

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.enums import EstadoPartidoEnum, TipoEventoEnum
from app.models.evento_partido_model import EventoPartidoModel
from app.models.fase_model import FaseModel
from app.models.jugador_model import JugadorModel
from app.models.partido_model import PartidoModel
from app.schemas.evento_partido_schema import EventoPartidoCreate


class EventoPartidoRepository:
    def __init__(self, db: Session):
        self.db = db

    def crear_evento(self, id_partido: int, datos: EventoPartidoCreate) -> EventoPartidoModel:
        """Inserta el evento sin commit (flush para tener su id): el servicio lo guarda junto con sus efectos."""
        evento = EventoPartidoModel(partido_id=id_partido, **datos.model_dump())
        self.db.add(evento)
        self.db.flush()
        return evento

    def confirmar(self) -> None:
        self.db.commit()

    def obtener_por_id(self, id_evento: int) -> EventoPartidoModel | None:
        return self.db.get(EventoPartidoModel, id_evento)

    def obtener_por_partido(self, id_partido: int) -> list[EventoPartidoModel]:
        """Línea de tiempo del partido, ordenada por minuto."""
        return (
            self.db.query(EventoPartidoModel)
            .filter(EventoPartidoModel.partido_id == id_partido)
            .order_by(EventoPartidoModel.minuto_ocurrencia, EventoPartidoModel.id)
            .all()
        )

    def obtener_cronologico_por_equipo(self, id_partido: int, id_equipo: int) -> list[EventoPartidoModel]:
        """Eventos del equipo en el orden en que se registraron (sirve para reconstruir quién está en cancha)."""
        return (
            self.db.query(EventoPartidoModel)
            .filter(EventoPartidoModel.partido_id == id_partido, EventoPartidoModel.equipo_id == id_equipo)
            .order_by(EventoPartidoModel.id)
            .all()
        )

    def contar_sustituciones(self, id_partido: int, id_equipo: int) -> int:
        return (
            self.db.query(func.count(EventoPartidoModel.id))
            .filter(
                EventoPartidoModel.partido_id == id_partido,
                EventoPartidoModel.equipo_id == id_equipo,
                EventoPartidoModel.tipo_evento == TipoEventoEnum.SUSTITUCION,
            )
            .scalar()
        )

    def contar_tarjetas_rojas(self, id_jugador: int, excluir_id: int | None = None) -> int:
        consulta = self.db.query(func.count(EventoPartidoModel.id)).filter(
            EventoPartidoModel.jugador_id == id_jugador,
            EventoPartidoModel.tipo_evento == TipoEventoEnum.TARJETA_ROJA,
        )
        if excluir_id is not None:
            consulta = consulta.filter(EventoPartidoModel.id != excluir_id)
        return consulta.scalar()

    def eliminar_evento(self, evento: EventoPartidoModel) -> None:
        """Borra el evento sin commit; el servicio lo guarda junto con la reversión de sus efectos."""
        self.db.delete(evento)

    def goleadores(self, id_torneo: int, limite: int = 10) -> list[tuple]:
        """(jugador_id, nombre, equipo_id, goles) de los partidos Finalizados del torneo.
        Los autogoles no cuentan. Orden: más goles primero y, a igualdad, el jugador inscrito antes."""
        goles = func.count(EventoPartidoModel.id)
        return (
            self.db.query(JugadorModel.id, JugadorModel.nombre_completo, EventoPartidoModel.equipo_id, goles)
            .join(EventoPartidoModel, EventoPartidoModel.jugador_id == JugadorModel.id)
            .join(PartidoModel, PartidoModel.id == EventoPartidoModel.partido_id)
            .join(FaseModel, FaseModel.id == PartidoModel.fase_id)
            .filter(
                FaseModel.torneo_id == id_torneo,
                PartidoModel.estado == EstadoPartidoEnum.FINALIZADO,
                EventoPartidoModel.tipo_evento == TipoEventoEnum.GOL,
            )
            .group_by(JugadorModel.id, JugadorModel.nombre_completo, EventoPartidoModel.equipo_id)
            .order_by(goles.desc(), JugadorModel.id)
            .limit(limite)
            .all()
        )
