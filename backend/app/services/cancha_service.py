"""Reglas de negocio de canchas."""

from datetime import date, datetime

from fastapi import HTTPException, status

from app.core.reglas import DURACION_PARTIDO_MIN
from app.models.cancha_model import CanchaModel
from app.models.partido_model import PartidoModel
from app.repositories.cancha_repository import CanchaRepository
from app.repositories.partido_repository import PartidoRepository
from app.schemas.cancha_schema import CanchaCreate, CanchaUpdate


class CanchaService:
    def __init__(self, repository: CanchaRepository, partido_repository: PartidoRepository):
        self.repository = repository
        self.partido_repository = partido_repository

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

    def verificar_disponibilidad(
        self,
        id_cancha: int,
        inicio: datetime,
        duracion_min: int = DURACION_PARTIDO_MIN,
        excluir_partido_id: int | None = None,
    ) -> bool:
        """True si la cancha está activa y ningún otro partido empieza a menos de `duracion_min` minutos
        del horario pedido. Un partido Suspendido libera su horario."""
        cancha = self.obtener_por_id(id_cancha)
        if not cancha.estado_activo:
            return False
        return self.partido_repository.cruce_en_cancha(id_cancha, inicio, duracion_min, excluir_partido_id) is None

    def obtener_agenda(self, id_cancha: int, fecha_consulta: date) -> list[PartidoModel]:
        """Partidos programados en esa cancha durante un día, en orden de hora."""
        self.obtener_por_id(id_cancha)
        return self.partido_repository.listar_por_cancha_y_fecha(id_cancha, fecha_consulta)
