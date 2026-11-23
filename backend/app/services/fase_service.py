"""Reglas de negocio de fases: se definen antes de que el torneo empiece."""

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.core.enums import (
    EstadoFaseEnum,
    EstadoPartidoEnum,
    EstadoTorneoEnum,
    TipoFormatoEnum,
)
from app.core.reglas import CLASIFICAN_POR_GRUPO, obtener_regla_entera
from app.models.fase_model import FaseModel
from app.models.partido_model import PartidoModel
from app.models.torneo_model import TorneoModel
from app.repositories.fase_repository import FaseRepository
from app.repositories.marcador_repository import MarcadorRepository
from app.repositories.partido_repository import PartidoRepository
from app.repositories.tabla_posiciones_repository import TablaPosicionesRepository
from app.repositories.torneo_repository import TorneoRepository
from app.schemas.fase_schema import ConfiguracionFases, FaseCreate
from app.services.tabla_posiciones_service import TablaPosicionesService

# Pendiente (Fase 5): generar_fixture, que arma los cruces con cancha y hora automáticamente.

_PARTIDO_TERMINADO = (EstadoPartidoEnum.FINALIZADO, EstadoPartidoEnum.W_O)


class FaseService:
    def __init__(
        self,
        repository: FaseRepository,
        torneo_repository: TorneoRepository,
        tabla_repository: TablaPosicionesRepository,
        partido_repository: PartidoRepository,
        marcador_repository: MarcadorRepository,
        tabla_service: TablaPosicionesService,
    ):
        self.repository = repository
        self.torneo_repository = torneo_repository
        self.tabla_repository = tabla_repository
        self.partido_repository = partido_repository
        self.marcador_repository = marcador_repository
        self.tabla_service = tabla_service

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

    def determinar_clasificados(self, id_fase: int) -> list[int]:
        """Equipos que avanzan: en fase de grupos, los primeros de cada grupo cerrado (grupo por grupo);
        en eliminatoria directa, los ganadores de cada partido, en el orden del calendario."""
        fase = self.obtener_por_id(id_fase)
        if fase.tipo_formato == TipoFormatoEnum.GRUPOS:
            tablas = self.tabla_repository.obtener_por_fase(fase.id)
            if not tablas:
                raise HTTPException(status.HTTP_409_CONFLICT, "La fase no tiene grupos.")
            if any(not tabla.estado_cierre for tabla in tablas):
                raise HTTPException(status.HTTP_409_CONFLICT, "Todos los grupos deben estar cerrados.")
            torneo = self._obtener_torneo(fase.torneo_id)
            cantidad = obtener_regla_entera(torneo, "clasifican_por_grupo", CLASIFICAN_POR_GRUPO)
            clasificados: list[int] = []
            for tabla in tablas:
                filas = self.tabla_service.calcular_clasificacion_actual(tabla.id)
                clasificados.extend(fila.equipo_id for fila in filas[:cantidad])
            return clasificados

        partidos = self._partidos_terminados(fase)
        return [self._ganador(partido) for partido in partidos]

    def cerrar_fase(self, id_fase: int) -> FaseModel:
        """Finaliza la fase si todos sus partidos terminaron (y, en grupos, todos los grupos están cerrados).
        Con esto se habilita programar la fase siguiente."""
        fase = self.obtener_por_id(id_fase)
        if fase.estado == EstadoFaseEnum.FINALIZADA:
            raise HTTPException(status.HTTP_409_CONFLICT, "La fase ya está Finalizada.")
        torneo = self._obtener_torneo(fase.torneo_id)
        if torneo.estado != EstadoTorneoEnum.EN_CURSO:
            raise HTTPException(status.HTTP_409_CONFLICT, "El torneo no está En_Curso.")
        self._partidos_terminados(fase)
        if fase.tipo_formato == TipoFormatoEnum.GRUPOS:
            tablas = self.tabla_repository.obtener_por_fase(fase.id)
            if not tablas or any(not tabla.estado_cierre for tabla in tablas):
                raise HTTPException(status.HTTP_409_CONFLICT, "Cierra primero todos los grupos de la fase.")
        return self.repository.actualizar_estado(fase.id, EstadoFaseEnum.FINALIZADA)

    # ---------- auxiliares ----------
    def _partidos_terminados(self, fase: FaseModel) -> list[PartidoModel]:
        """Los partidos de la fase, exigiendo que existan y que todos hayan terminado."""
        partidos = self.partido_repository.listar_por_fase(fase.id)
        if not partidos:
            raise HTTPException(status.HTTP_409_CONFLICT, "La fase no tiene partidos.")
        if any(partido.estado not in _PARTIDO_TERMINADO for partido in partidos):
            raise HTTPException(status.HTTP_409_CONFLICT, "Aún hay partidos de la fase sin finalizar.")
        return partidos

    def _ganador(self, partido: PartidoModel) -> int:
        marcador = self.marcador_repository.obtener_por_partido(partido.id)
        if marcador.goles_local != marcador.goles_visitante:
            local_gana = marcador.goles_local > marcador.goles_visitante
        elif (
            marcador.goles_penales_local is not None
            and marcador.goles_penales_visitante is not None
            and marcador.goles_penales_local != marcador.goles_penales_visitante
        ):
            local_gana = marcador.goles_penales_local > marcador.goles_penales_visitante
        else:
            raise HTTPException(status.HTTP_409_CONFLICT, "Un partido empatado no tiene ganador definido.")
        return partido.equipo_local_id if local_gana else partido.equipo_visitante_id

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
