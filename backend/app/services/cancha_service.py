"""Reglas de negocio de canchas."""

from fastapi import HTTPException, status

from app.models.cancha_model import CanchaModel
from app.repositories.cancha_repository import CanchaRepository
from app.schemas.cancha_schema import CanchaCreate, CanchaUpdate

# Pendiente (Fase 4): verificar_disponibilidad y obtener_agenda, que consultan la tabla Partido.


class CanchaService:
    def __init__(self, repository: CanchaRepository):
        self.repository = repository

    def crear_cancha(self, datos_cancha: CanchaCreate) -> CanchaModel:
        return self.repository.crear_cancha(datos_cancha)

    def obtener_por_id(self, id_cancha: int) -> CanchaModel:
        cancha = self.repository.obtener_por_id(id_cancha)
        if cancha is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "La cancha solicitada no existe.")
        return cancha

    def obtener_todas(self, solo_activas: bool = True) -> list[CanchaModel]:
        return self.repository.obtener_todas(solo_activas)

    def actualizar_detalles(self, id_cancha: int, datos: CanchaUpdate) -> CanchaModel:
        cancha = self.repository.actualizar_detalles(id_cancha, datos)
        if cancha is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "La cancha solicitada no existe.")
        return cancha

    def modificar_estado(self, id_cancha: int, activo: bool) -> CanchaModel:
        cancha = self.repository.modificar_estado(id_cancha, activo)
        if cancha is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "La cancha solicitada no existe.")
        return cancha
