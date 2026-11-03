"""Valida las referencias del equipo y la plantilla antes de persistir."""
from fastapi import HTTPException
from app.models.colegio_model import ColegioModel
from app.models.usuario_model import EntrenadorModel
from app.services.transaction import transaccion


class EquipoService:
    def __init__(self, repository):
        self.repository = repository

    @transaccion
    def crear_equipo(self, datos):
        colegio = self.repository.db.get(ColegioModel, datos.colegio_id)
        entrenador = self.repository.db.get(EntrenadorModel, datos.entrenador_id)
        if colegio is None or entrenador is None:
            raise HTTPException(404, "Colegio o entrenador no existe.")
        if not colegio.estado_activo or not entrenador.estado_activo:
            raise HTTPException(409, "El colegio y el entrenador deben estar activos.")
        return self.repository.crear_equipo(datos)

    def obtener_equipos(self, colegio_id=None):
        return self.repository.obtener_equipos(colegio_id)

    def obtener_equipo(self, id_equipo):
        equipo = self.repository.obtener_equipo(id_equipo)
        if equipo is None:
            raise HTTPException(404, "Equipo no existe.")
        return equipo

    @transaccion
    def crear_jugador(self, datos):
        equipo = self.obtener_equipo(datos.equipo_id)
        if not equipo.estado_activo:
            raise HTTPException(409, "El equipo está inactivo.")
        return self.repository.crear_jugador(datos)

    def obtener_jugadores(self, id_equipo):
        self.obtener_equipo(id_equipo)
        return self.repository.obtener_jugadores(id_equipo)
