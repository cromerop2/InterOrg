"""El día del partido: inicio, marcador del árbitro, cierre de acta y W.O."""

from fastapi import HTTPException, status

from app.core.enums import (
    EstadoFaseEnum,
    EstadoPartidoEnum,
    EstadoTorneoEnum,
    TipoFormatoEnum,
)
from app.core.reglas import GOLES_WALKOVER, PUNTOS_EMPATE, PUNTOS_VICTORIA, obtener_regla_entera
from app.models.marcador_model import MarcadorModel
from app.models.partido_model import PartidoModel
from app.repositories.fase_repository import FaseRepository
from app.repositories.partido_repository import PartidoRepository
from app.repositories.tabla_posiciones_repository import TablaPosicionesRepository
from app.repositories.torneo_repository import TorneoRepository
from app.schemas.marcador_schema import MarcadorUpdate
from app.services.alineacion_service import AlineacionService
from app.services.fila_posicion_service import FilaPosicionService
from app.services.marcador_service import MarcadorService

# Pendiente (Fase 5): modificar_acta_cerrada, que usa revertir_resultado_partido para corregir un acta.


class JuegoService:
    def __init__(
        self,
        repository: PartidoRepository,
        marcador_service: MarcadorService,
        alineacion_service: AlineacionService,
        fase_repository: FaseRepository,
        torneo_repository: TorneoRepository,
        tabla_repository: TablaPosicionesRepository,
        fila_service: FilaPosicionService,
    ):
        self.repository = repository
        self.marcador_service = marcador_service
        self.alineacion_service = alineacion_service
        self.fase_repository = fase_repository
        self.torneo_repository = torneo_repository
        self.tabla_repository = tabla_repository
        self.fila_service = fila_service

    # ---------- árbitro ----------
    def iniciar_partido(self, id_partido: int, arbitro) -> PartidoModel:
        """Pasa el partido de "Programado" a "En_Juego" si ambos equipos enviaron su alineación."""
        partido, fase, _ = self._partido_del_arbitro(id_partido, arbitro, EstadoPartidoEnum.PROGRAMADO)
        if not self.alineacion_service.validar_alineaciones(partido.id):
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "Falta la alineación de uno de los equipos; el administrador puede decretar W.O.",
            )
        if fase.estado == EstadoFaseEnum.PROGRAMADA:
            self.fase_repository.actualizar_estado(fase.id, EstadoFaseEnum.EN_JUEGO, confirmar=False)
        # Comparten sesión: este commit guarda también el cambio de la fase.
        return self.repository.actualizar_estado(partido.id, EstadoPartidoEnum.EN_JUEGO)

    def registrar_marcador(self, id_partido: int, datos: MarcadorUpdate, arbitro) -> MarcadorModel:
        """Guarda el resultado numérico mientras el partido está En_Juego."""
        partido, fase, _ = self._partido_del_arbitro(id_partido, arbitro, EstadoPartidoEnum.EN_JUEGO)
        if datos.goles_penales_local is not None and fase.tipo_formato != TipoFormatoEnum.ELIMINATORIA_DIRECTA:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "Los penales solo se registran en fases de eliminatoria directa."
            )
        return self.marcador_service.actualizar_goles(
            partido.id,
            datos.goles_local,
            datos.goles_visitante,
            datos.goles_penales_local,
            datos.goles_penales_visitante,
        )

    def cerrar_acta_oficial(self, id_partido: int, arbitro) -> PartidoModel:
        """Cierra el acta: el partido queda "Finalizado", el marcador definitivo y la tabla de posiciones al día."""
        partido, fase, torneo = self._partido_del_arbitro(id_partido, arbitro, EstadoPartidoEnum.EN_JUEGO)
        if self.marcador_service.validar_necesidad_desempate(partido.id):
            marcador = self.marcador_service.obtener_por_partido(partido.id)
            local, visitante = marcador.goles_penales_local, marcador.goles_penales_visitante
            if local is None or visitante is None or local == visitante:
                raise HTTPException(
                    status.HTTP_409_CONFLICT,
                    "El partido terminó empatado en una eliminatoria: registra los penales con un ganador.",
                )
        return self.finalizar_encuentro(partido, fase, torneo, EstadoPartidoEnum.FINALIZADO)

    # ---------- Administrador ----------
    def aplicar_walkover(self, id_partido: int, id_equipo_ganador: int) -> PartidoModel:
        """Decreta W.O. a favor del equipo presente: marcador 3-0 (configurable) y resultado definitivo."""
        partido = self.repository.obtener_por_id(id_partido)
        if partido is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "El partido solicitado no existe.")
        fase, torneo = self._fase_y_torneo(partido)
        if torneo.estado != EstadoTorneoEnum.EN_CURSO:
            raise HTTPException(status.HTTP_409_CONFLICT, "El torneo no está En_Curso.")
        if partido.estado != EstadoPartidoEnum.PROGRAMADO:
            raise HTTPException(status.HTTP_409_CONFLICT, "Solo se decreta W.O. en un partido Programado.")
        if id_equipo_ganador not in (partido.equipo_local_id, partido.equipo_visitante_id):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "El ganador debe ser uno de los dos equipos del partido.")

        goles = obtener_regla_entera(torneo, "goles_walkover", GOLES_WALKOVER)
        gana_local = id_equipo_ganador == partido.equipo_local_id
        self.marcador_service.actualizar_goles(
            partido.id, goles if gana_local else 0, 0 if gana_local else goles, confirmar=False
        )
        if fase.estado == EstadoFaseEnum.PROGRAMADA:
            self.fase_repository.actualizar_estado(fase.id, EstadoFaseEnum.EN_JUEGO, confirmar=False)
        return self.finalizar_encuentro(partido, fase, torneo, EstadoPartidoEnum.W_O)

    # ---------- cierre ----------
    def finalizar_encuentro(self, partido: PartidoModel, fase, torneo, estado_final: EstadoPartidoEnum) -> PartidoModel:
        """Orquesta el cierre: fija el marcador, actualiza la tabla (si es fase de grupos) y cambia el estado.
        Todo se guarda en un solo commit: o se aplica completo o no se aplica nada."""
        marcador = self.marcador_service.obtener_por_partido(partido.id)
        self.marcador_service.fijar_resultado_final(partido.id, confirmar=False)

        if fase.tipo_formato == TipoFormatoEnum.GRUPOS:
            tabla = self.tabla_repository.obtener_por_fase_y_equipo(fase.id, partido.equipo_local_id)
            if tabla is None:
                raise HTTPException(status.HTTP_409_CONFLICT, "Los equipos del partido no están en ningún grupo.")
            victoria = obtener_regla_entera(torneo, "puntos_victoria", PUNTOS_VICTORIA)
            empate = obtener_regla_entera(torneo, "puntos_empate", PUNTOS_EMPATE)
            gl, gv = marcador.goles_local, marcador.goles_visitante
            self.fila_service.procesar_resultado_partido(
                tabla.id, partido.equipo_local_id, gl, gv, victoria, empate, confirmar=False
            )
            self.fila_service.procesar_resultado_partido(
                tabla.id, partido.equipo_visitante_id, gv, gl, victoria, empate, confirmar=False
            )
        return self.repository.actualizar_estado(partido.id, estado_final)  # commit de todo lo pendiente

    # ---------- auxiliares ----------
    def _fase_y_torneo(self, partido: PartidoModel):
        fase = self.fase_repository.obtener_por_id(partido.fase_id)
        return fase, self.torneo_repository.obtener_por_id(fase.torneo_id)

    def _partido_del_arbitro(self, id_partido: int, arbitro, estado_requerido: EstadoPartidoEnum):
        partido = self.repository.obtener_por_id(id_partido)
        if partido is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "El partido solicitado no existe.")
        if partido.arbitro_id != arbitro.id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "No eres el árbitro designado de este partido.")
        if partido.estado != estado_requerido:
            raise HTTPException(
                status.HTTP_409_CONFLICT, f"El partido debe estar {estado_requerido.value} para esta acción."
            )
        fase, torneo = self._fase_y_torneo(partido)
        if torneo.estado != EstadoTorneoEnum.EN_CURSO:
            raise HTTPException(status.HTTP_409_CONFLICT, "El torneo no está En_Curso.")
        return partido, fase, torneo
