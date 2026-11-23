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
        if not estado:
            jugador.fechas_suspension = 0  # levantar la sanción borra las fechas pendientes
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

    def aplicar_sancion(self, id_jugador: int, fechas: int, confirmar: bool = True) -> JugadorModel | None:
        """Suma `fechas` de suspensión y deja al jugador sancionado."""
        jugador = self.obtener_por_id(id_jugador)
        if jugador is None:
            return None
        jugador.fechas_suspension = (jugador.fechas_suspension or 0) + fechas
        jugador.sancionado = True
        if confirmar:
            self.db.commit()
            self.db.refresh(jugador)
        return jugador

    def reducir_suspension(self, id_jugador: int, fechas: int, confirmar: bool = True) -> JugadorModel | None:
        """Resta fechas de suspensión (p. ej. al borrar una tarjeta roja registrada por error)."""
        jugador = self.obtener_por_id(id_jugador)
        if jugador is None:
            return None
        jugador.fechas_suspension = max(0, (jugador.fechas_suspension or 0) - fechas)
        if jugador.fechas_suspension == 0:
            jugador.sancionado = False
        if confirmar:
            self.db.commit()
            self.db.refresh(jugador)
        return jugador

    def descontar_fecha_suspension(self, id_equipo: int, excluir_ids: set[int], confirmar: bool = True) -> None:
        """Tras un partido del equipo, cada jugador con fechas pendientes cumple una (salvo los de `excluir_ids`,
        por ejemplo quienes fueron expulsados en ese mismo partido). Al llegar a 0 queda libre."""
        suspendidos = (
            self.db.query(JugadorModel)
            .filter(JugadorModel.equipo_id == id_equipo, JugadorModel.fechas_suspension > 0)
            .all()
        )
        for jugador in suspendidos:
            if jugador.id in excluir_ids:
                continue
            jugador.fechas_suspension -= 1
            if jugador.fechas_suspension == 0:
                jugador.sancionado = False
        if confirmar:
            self.db.commit()
