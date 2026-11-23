"""Acceso a la BD para jugadores."""

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.equipo_model import EquipoModel
from app.models.jugador_model import JugadorModel
from app.schemas.jugador_schema import JugadorCreate


class JugadorRepository:
    def __init__(self, db: Session):
        self.db = db

    def crear_jugador(self, id_equipo: int, datos_jugador: JugadorCreate) -> JugadorModel:
        jugador = JugadorModel(equipo_id=id_equipo, **datos_jugador.model_dump())
        self.db.add(jugador)
        self.db.commit()
        self.db.refresh(jugador)
        return jugador

    def obtener_por_id(self, id_jugador: int) -> JugadorModel | None:
        return self.db.get(JugadorModel, id_jugador)

    def obtener_por_identificacion_en_torneo(
        self, identificacion: str, id_torneo: int
    ) -> JugadorModel | None:
        """Jugador ACTIVO con ese documento en cualquier equipo del torneo (para evitar inscribirlo dos veces)."""
        return (
            self.db.query(JugadorModel)
            .join(EquipoModel, EquipoModel.id == JugadorModel.equipo_id)
            .filter(
                JugadorModel.identificacion == identificacion,
                JugadorModel.estado_activo.is_(True),
                EquipoModel.torneo_id == id_torneo,
            )
            .first()
        )

    def obtener_por_equipo(self, id_equipo: int, solo_activos: bool = True) -> list[JugadorModel]:
        consulta = self.db.query(JugadorModel).filter(JugadorModel.equipo_id == id_equipo)
        if solo_activos:
            consulta = consulta.filter(JugadorModel.estado_activo.is_(True))
        return consulta.order_by(JugadorModel.id).all()

    def contar_activos(self, id_equipo: int) -> int:
        return (
            self.db.query(func.count(JugadorModel.id))
            .filter(JugadorModel.equipo_id == id_equipo, JugadorModel.estado_activo.is_(True))
            .scalar()
        )

    def actualizar_estado_sancion(
        self, id_jugador: int, estado: bool, confirmar: bool = True
    ) -> JugadorModel | None:
        jugador = self.obtener_por_id(id_jugador)
        if jugador is None:
            return None
        jugador.sancionado = estado
        if confirmar:
            self.db.commit()
            self.db.refresh(jugador)
        return jugador

    def dar_de_baja(self, id_jugador: int) -> JugadorModel | None:
        """Desactiva al jugador sin borrar su historial."""
        jugador = self.obtener_por_id(id_jugador)
        if jugador is None:
            return None
        jugador.estado_activo = False
        self.db.commit()
        self.db.refresh(jugador)
        return jugador

    def mover_a_equipo(self, id_jugador: int, id_equipo_destino: int) -> JugadorModel | None:
        jugador = self.obtener_por_id(id_jugador)
        if jugador is None:
            return None
        jugador.equipo_id = id_equipo_destino
        self.db.commit()
        self.db.refresh(jugador)
        return jugador
