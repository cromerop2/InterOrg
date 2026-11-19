"""Reglas de negocio de fases: se definen antes de que el torneo empiece."""

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.core.enums import EstadoTorneoEnum
from app.models.fase_model import FaseModel
from app.models.torneo_model import TorneoModel
from app.repositories.fase_repository import FaseRepository
from app.repositories.torneo_repository import TorneoRepository
from app.schemas.fase_schema import ConfiguracionFases, FaseCreate

# Pendiente (Fases 3 y 4): generar_fixture, determinar_clasificados y cerrar_fase,
# que dependen de Equipo, Partido y TablaPosiciones.


class FaseService:
    def __init__(self, repository: FaseRepository, torneo_repository: TorneoRepository):
        self.repository = repository
        self.torneo_repository = torneo_repository

    def crear_fase(self, id_torneo: int, datos_fase: FaseCreate) -> FaseModel:
        self._validar_torneo_editable(id_torneo)
        self._validar_nombre_disponible(id_torneo, datos_fase.nombre)
        try:
            return self.repository.crear_fase(id_torneo, datos_fase)
        except IntegrityError:
            # Otra petición creó el mismo nombre entre la validación y el guardado.
            self._validar_nombre_disponible(id_torneo, datos_fase.nombre)
            raise

    def estructurar_fases(self, id_torneo: int, configuracion: ConfiguracionFases) -> list[FaseModel]:
        """Crea de una vez todas las fases del torneo, en el orden recibido."""
        self._validar_torneo_editable(id_torneo)
        if self.repository.obtener_por_torneo(id_torneo):
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "El torneo ya tiene fases; agrégalas una a una con POST /torneos/{id}/fases.",
            )
        return self.repository.crear_varias(id_torneo, configuracion.fases)

    def obtener_por_torneo(self, id_torneo: int) -> list[FaseModel]:
        self._obtener_torneo(id_torneo)
        return self.repository.obtener_por_torneo(id_torneo)

    def obtener_por_id(self, id_fase: int) -> FaseModel:
        fase = self.repository.obtener_por_id(id_fase)
        if fase is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "La fase solicitada no existe.")
        return fase

    # ---------- auxiliares ----------
    def _obtener_torneo(self, id_torneo: int) -> TorneoModel:
        torneo = self.torneo_repository.obtener_por_id(id_torneo)
        if torneo is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "El torneo solicitado no existe.")
        return torneo

    def _validar_torneo_editable(self, id_torneo: int) -> None:
        torneo = self._obtener_torneo(id_torneo)
        if torneo.estado != EstadoTorneoEnum.INSCRIPCIONES:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "Solo se pueden definir fases mientras el torneo está en Inscripciones.",
            )

    def _validar_nombre_disponible(self, id_torneo: int, nombre: str) -> None:
        if self.repository.obtener_por_nombre(id_torneo, nombre):
            raise HTTPException(
                status.HTTP_409_CONFLICT, "El torneo ya tiene una fase con ese nombre."
            )
