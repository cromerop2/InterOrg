"""Corrección de actas cerradas: solo el Administrador, con motivo y registro de auditoría."""

from fastapi import HTTPException, status

from app.core.enums import (
    EstadoFaseEnum,
    EstadoPartidoEnum,
    EstadoTorneoEnum,
    TipoFormatoEnum,
)
from app.core.reglas import GOLES_WALKOVER, PUNTOS_EMPATE, PUNTOS_VICTORIA, obtener_regla_entera
from app.models.auditoria_acta_model import AuditoriaActaModel
from app.models.marcador_model import MarcadorModel
from app.models.partido_model import PartidoModel
from app.repositories.auditoria_acta_repository import AuditoriaActaRepository
from app.repositories.fase_repository import FaseRepository
from app.repositories.partido_repository import PartidoRepository
from app.repositories.tabla_posiciones_repository import TablaPosicionesRepository
from app.repositories.torneo_repository import TorneoRepository
from app.schemas.acta_schema import ActaCorreccion
from app.services.fila_posicion_service import FilaPosicionService
from app.services.marcador_service import MarcadorService


class ActaService:
    def __init__(
        self,
        repository: AuditoriaActaRepository,
        partido_repository: PartidoRepository,
        marcador_service: MarcadorService,
        fase_repository: FaseRepository,
        torneo_repository: TorneoRepository,
        tabla_repository: TablaPosicionesRepository,
        fila_service: FilaPosicionService,
    ):
        self.repository = repository
        self.partido_repository = partido_repository
        self.marcador_service = marcador_service
        self.fase_repository = fase_repository
        self.torneo_repository = torneo_repository
        self.tabla_repository = tabla_repository
        self.fila_service = fila_service

    def modificar_acta_cerrada(self, id_partido: int, datos: ActaCorreccion, administrador) -> PartidoModel:
        """Corrige un acta cerrada: cambia el marcador o decreta W.O., ajusta la tabla de posiciones
        (revierte el resultado viejo y suma el nuevo) y deja constancia con el motivo. Todo en un solo commit."""
        partido = self.partido_repository.obtener_por_id(id_partido)
        if partido is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "El partido solicitado no existe.")
        fase = self.fase_repository.obtener_por_id(partido.fase_id)
        torneo = self.torneo_repository.obtener_por_id(fase.torneo_id)
        if torneo.estado != EstadoTorneoEnum.EN_CURSO:
            raise HTTPException(status.HTTP_409_CONFLICT, "El torneo ya no admite correcciones.")
        if fase.estado == EstadoFaseEnum.FINALIZADA:
            raise HTTPException(status.HTTP_409_CONFLICT, "La fase ya finalizó: sus actas no se corrigen.")
        if partido.estado not in (EstadoPartidoEnum.FINALIZADO, EstadoPartidoEnum.W_O):
            raise HTTPException(status.HTTP_409_CONFLICT, "Solo se corrige un acta ya cerrada.")

        marcador = self.marcador_service.obtener_por_partido(partido.id)
        anterior = self._instantanea(partido.estado, marcador.goles_local, marcador.goles_visitante,
                                     marcador.goles_penales_local, marcador.goles_penales_visitante)
        nuevo_estado, goles_local, goles_visitante, penales_local, penales_visitante = self._resultado_nuevo(
            partido, fase, torneo, datos
        )

        tabla = None
        if fase.tipo_formato == TipoFormatoEnum.GRUPOS:
            tabla = self.tabla_repository.obtener_por_fase_y_equipo(fase.id, partido.equipo_local_id)
            if tabla is None:
                raise HTTPException(status.HTTP_409_CONFLICT, "Los equipos del partido no están en ningún grupo.")
            if tabla.estado_cierre:
                raise HTTPException(
                    status.HTTP_409_CONFLICT, "El grupo está cerrado: reábrelo (POST /tablas/{id}/reabrir) antes de corregir."
                )
            victoria = obtener_regla_entera(torneo, "puntos_victoria", PUNTOS_VICTORIA)
            empate = obtener_regla_entera(torneo, "puntos_empate", PUNTOS_EMPATE)
            for id_equipo, propios, rivales, nuevos_propios, nuevos_rivales in (
                (partido.equipo_local_id, marcador.goles_local, marcador.goles_visitante, goles_local, goles_visitante),
                (partido.equipo_visitante_id, marcador.goles_visitante, marcador.goles_local, goles_visitante, goles_local),
            ):
                self.fila_service.revertir_resultado_partido(tabla.id, id_equipo, propios, rivales, victoria, empate, confirmar=False)
                self.fila_service.procesar_resultado_partido(tabla.id, id_equipo, nuevos_propios, nuevos_rivales, victoria, empate, confirmar=False)

        self.marcador_service.corregir_resultado(
            partido.id, goles_local, goles_visitante, penales_local, penales_visitante, confirmar=False
        )
        self.partido_repository.actualizar_estado(partido.id, nuevo_estado, confirmar=False)
        nuevo = self._instantanea(nuevo_estado, goles_local, goles_visitante, penales_local, penales_visitante)
        # Comparten sesión: este commit guarda la corrección y su auditoría a la vez.
        self.repository.registrar(partido.id, administrador.id, datos.motivo_auditoria, anterior, nuevo)
        return self.partido_repository.obtener_por_id(partido.id)

    def obtener_auditoria(self, id_partido: int) -> list[AuditoriaActaModel]:
        if self.partido_repository.obtener_por_id(id_partido) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "El partido solicitado no existe.")
        return self.repository.obtener_por_partido(id_partido)

    # ---------- auxiliares ----------
    def _resultado_nuevo(self, partido, fase, torneo, datos: ActaCorreccion):
        """Devuelve (estado, goles_local, goles_visitante, penales_local, penales_visitante) ya validados."""
        if datos.walkover_ganador_id is not None:
            if datos.walkover_ganador_id not in (partido.equipo_local_id, partido.equipo_visitante_id):
                raise HTTPException(status.HTTP_400_BAD_REQUEST, "El ganador debe ser uno de los dos equipos del partido.")
            goles = obtener_regla_entera(torneo, "goles_walkover", GOLES_WALKOVER)
            gana_local = datos.walkover_ganador_id == partido.equipo_local_id
            return EstadoPartidoEnum.W_O, (goles if gana_local else 0), (0 if gana_local else goles), None, None

        if partido.estado == EstadoPartidoEnum.W_O:
            raise HTTPException(
                status.HTTP_409_CONFLICT, "Un partido decidido por W.O. solo se corrige cambiando el equipo ganador."
            )
        local, visitante = datos.goles_local, datos.goles_visitante
        penales_local, penales_visitante = datos.goles_penales_local, datos.goles_penales_visitante
        if fase.tipo_formato == TipoFormatoEnum.ELIMINATORIA_DIRECTA:
            if local == visitante:
                if penales_local is None or penales_local == penales_visitante:
                    raise HTTPException(
                        status.HTTP_400_BAD_REQUEST, "Un empate en eliminatoria exige penales con un ganador."
                    )
            else:
                penales_local = penales_visitante = None  # ya no hay empate: los penales sobran
        elif penales_local is not None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Los penales solo se registran en eliminatorias.")
        return EstadoPartidoEnum.FINALIZADO, local, visitante, penales_local, penales_visitante

    @staticmethod
    def _instantanea(estado, goles_local, goles_visitante, penales_local, penales_visitante) -> dict:
        return {
            "estado": estado.value,
            "goles_local": goles_local,
            "goles_visitante": goles_visitante,
            "goles_penales_local": penales_local,
            "goles_penales_visitante": penales_visitante,
        }
