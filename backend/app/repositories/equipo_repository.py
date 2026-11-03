"""Persistencia del catálogo de equipos y sus plantillas."""
from app.models.equipo_model import EquipoModel
from app.models.jugador_model import JugadorModel


class EquipoRepository:
    def __init__(self, db):
        self.db = db

    def crear_equipo(self, datos):
        equipo = EquipoModel(**datos.model_dump())
        self.db.add(equipo)
        self.db.flush()
        return equipo

    def obtener_equipos(self, colegio_id=None):
        consulta = self.db.query(EquipoModel)
        if colegio_id is not None:
            consulta = consulta.filter_by(colegio_id=colegio_id)
        return consulta.order_by(EquipoModel.id).all()

    def obtener_equipo(self, id_equipo):
        return self.db.get(EquipoModel, id_equipo)

    def crear_jugador(self, datos):
        jugador = JugadorModel(**datos.model_dump())
        self.db.add(jugador)
        self.db.flush()
        return jugador

    def obtener_jugadores(self, id_equipo):
        return self.db.query(JugadorModel).filter_by(equipo_id=id_equipo).order_by(JugadorModel.id).all()
