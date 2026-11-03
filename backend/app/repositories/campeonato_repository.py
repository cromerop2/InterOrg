"""Acceso SQL del campeonato. Los métodos públicos se reflejan en el router.

Las escrituras hacen flush; el servicio confirma al finalizar toda la operación.
Así generar un fixture o avanzar una ronda nunca deja registros a medias.
"""
from sqlalchemy import or_
from app.models.torneo_model import TorneoModel
from app.models.equipo_model import EquipoModel
from app.models.inscripcion_model import InscripcionModel
from app.models.fase_model import FaseModel
from app.models.grupo_model import GrupoModel
from app.models.partido_model import PartidoModel


class CampeonatoRepository:
    def __init__(self, db):
        self.db = db

    def obtener_torneos(self, estado=None):
        consulta = self.db.query(TorneoModel)
        if estado is not None:
            consulta = consulta.filter_by(estado=estado)
        return consulta.order_by(TorneoModel.id.desc()).all()

    def obtener_torneo(self, id_torneo, bloquear=False):
        consulta = self.db.query(TorneoModel).filter_by(id=id_torneo)
        if bloquear:
            consulta = consulta.with_for_update()
        return consulta.populate_existing().first()

    def crear_torneo(self, datos):
        torneo = TorneoModel(**datos.model_dump())
        self.db.add(torneo)
        self.db.flush()
        return torneo

    def obtener_inscripciones(self, id_torneo):
        return self.db.query(InscripcionModel).filter_by(torneo_id=id_torneo).order_by(InscripcionModel.id).all()

    def inscribir_equipo(self, id_torneo, id_equipo):
        inscripcion = InscripcionModel(torneo_id=id_torneo, equipo_id=id_equipo)
        self.db.add(inscripcion)
        self.db.flush()
        return inscripcion

    def retirar_equipo(self, inscripcion):
        self.db.delete(inscripcion)
        self.db.flush()

    def generar_fixture(self, fase, grupos, partidos):
        """Persiste los objetos preparados por el algoritmo del servicio."""
        self.db.add(fase)
        self.db.flush()
        for grupo, inscripciones in grupos:
            grupo.fase_id = fase.id
            self.db.add(grupo)
            self.db.flush()
            for inscripcion in inscripciones:
                inscripcion.grupo_id = grupo.id
        for partido, grupo in partidos:
            partido.fase_id = fase.id
            partido.grupo_id = grupo.id
            self.db.add(partido)
        self.db.flush()

    def avanzar_fase(self, fase, partidos):
        self.db.add(fase)
        self.db.flush()
        for partido in partidos:
            partido.fase_id = fase.id
            self.db.add(partido)
        self.db.flush()

    def obtener_fixture(self, id_torneo, equipo_id=None, fase_id=None):
        consulta = self.db.query(PartidoModel).filter_by(torneo_id=id_torneo)
        if equipo_id is not None:
            consulta = consulta.filter(or_(PartidoModel.equipo_local_id == equipo_id,
                                           PartidoModel.equipo_visitante_id == equipo_id))
        if fase_id is not None:
            consulta = consulta.filter_by(fase_id=fase_id)
        return consulta.order_by(PartidoModel.fase_id, PartidoModel.jornada, PartidoModel.numero).all()

    def obtener_posiciones(self, id_torneo):
        """Entrega grupos y equipos inscritos; los puntos se calculan en el servicio."""
        return self.db.query(GrupoModel).join(FaseModel).filter(
            FaseModel.torneo_id == id_torneo).order_by(GrupoModel.id).all()

    def obtener_seguimiento(self, id_torneo):
        return self.db.query(FaseModel).filter_by(torneo_id=id_torneo).order_by(FaseModel.orden).all()

    def programar_partido(self, partido, fecha_hora, sede):
        partido.fecha_hora, partido.sede = fecha_hora, sede
        self.db.flush()
        return partido

    def registrar_resultado(self, partido, datos):
        for campo, valor in datos.model_dump().items():
            setattr(partido, campo, valor)
        partido.estado = "Finalizado"
        self.db.flush()
        return partido

    def _partido(self, id_partido):
        return self.db.get(PartidoModel, id_partido)

    def _equipos(self, ids):
        return {e.id: e for e in self.db.query(EquipoModel).filter(EquipoModel.id.in_(ids)).all()}
