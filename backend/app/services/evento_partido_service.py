"""Reglas de negocio de los eventos de un partido: lo que el árbitro registra en tiempo real."""

from fastapi import HTTPException, status

from app.core.enums import EstadoPartidoEnum, EstadoTorneoEnum, TipoEventoEnum
from app.core.reglas import MAXIMO_SUSTITUCIONES, obtener_regla_entera
from app.models.evento_partido_model import EventoPartidoModel
from app.models.partido_model import PartidoModel
from app.repositories.alineacion_repository import AlineacionRepository
from app.repositories.evento_partido_repository import EventoPartidoRepository
from app.repositories.fase_repository import FaseRepository
from app.repositories.jugador_repository import JugadorRepository
from app.repositories.partido_repository import PartidoRepository
from app.repositories.torneo_repository import TorneoRepository
from app.schemas.evento_partido_schema import EventoPartidoCreate
from app.services.marcador_service import MarcadorService


class _EstadoEnCancha:
    """Quién puede actuar en el campo, reconstruido con la alineación y los eventos ya registrados."""

    def __init__(self, alineacion, eventos):
        self.convocados = {a.jugador_id for a in alineacion}
        self.suplentes = {a.jugador_id for a in alineacion if not a.es_titular}
        self.en_cancha = {a.jugador_id for a in alineacion if a.es_titular}
        self.ya_entraron: set[int] = set()
        self.expulsados: set[int] = set()
        for evento in eventos:  # en el orden en que se registraron
            if evento.tipo_evento == TipoEventoEnum.SUSTITUCION:
                self.en_cancha.discard(evento.jugador_secundario_id)
                self.en_cancha.add(evento.jugador_id)
                self.ya_entraron.add(evento.jugador_id)
            elif evento.tipo_evento == TipoEventoEnum.TARJETA_ROJA:
                self.en_cancha.discard(evento.jugador_id)
                self.expulsados.add(evento.jugador_id)


class EventoPartidoService:
    def __init__(
        self,
        repository: EventoPartidoRepository,
        partido_repository: PartidoRepository,
        alineacion_repository: AlineacionRepository,
        jugador_repository: JugadorRepository,
        fase_repository: FaseRepository,
        torneo_repository: TorneoRepository,
        marcador_service: MarcadorService,
    ):
        self.repository = repository
        self.partido_repository = partido_repository
        self.alineacion_repository = alineacion_repository
        self.jugador_repository = jugador_repository
        self.fase_repository = fase_repository
        self.torneo_repository = torneo_repository
        self.marcador_service = marcador_service

    # ---------- árbitro ----------
    def registrar_incidencia(self, id_partido: int, datos: EventoPartidoCreate, arbitro) -> EventoPartidoModel:
        """Valida el evento contra la alineación y el estado del campo, y lo guarda junto con sus efectos."""
        partido, torneo = self._partido_en_juego(id_partido, arbitro)
        if datos.equipo_id not in (partido.equipo_local_id, partido.equipo_visitante_id):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Ese equipo no juega este partido.")

        alineacion = self.alineacion_repository.obtener_por_partido_y_equipo(partido.id, datos.equipo_id)
        eventos = self.repository.obtener_cronologico_por_equipo(partido.id, datos.equipo_id)
        estado = _EstadoEnCancha(alineacion, eventos)

        if datos.jugador_id not in estado.convocados:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "El jugador no está en la alineación oficial de ese equipo en este partido."
            )

        if datos.tipo_evento == TipoEventoEnum.SUSTITUCION:
            self.validar_sustitucion(partido, datos, estado, torneo)
        elif datos.tipo_evento in (TipoEventoEnum.TARJETA_AMARILLA, TipoEventoEnum.TARJETA_ROJA):
            if datos.jugador_id in estado.expulsados:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, "Ese jugador ya fue expulsado.")
        else:  # Gol, Asistencia y Autogol los hace quien está jugando
            self._exigir_en_cancha(datos.jugador_id, estado)
            if datos.jugador_secundario_id is not None:  # asistente del gol
                if datos.jugador_secundario_id not in estado.convocados:
                    raise HTTPException(
                        status.HTTP_400_BAD_REQUEST, "El asistente no está en la alineación de ese equipo."
                    )
                self._exigir_en_cancha(datos.jugador_secundario_id, estado)

        evento = self.repository.crear_evento(partido.id, datos)
        self.procesar_efecto_secundario(evento, partido)
        self.repository.confirmar()  # el evento y sus efectos se guardan juntos
        return evento

    def validar_sustitucion(self, partido: PartidoModel, datos: EventoPartidoCreate, estado: _EstadoEnCancha, torneo) -> None:
        """Entra un suplente que no haya jugado, sale alguien que está en cancha y no se supera el máximo de cambios."""
        maximo = obtener_regla_entera(torneo, "max_sustituciones", MAXIMO_SUSTITUCIONES)
        if self.repository.contar_sustituciones(partido.id, datos.equipo_id) >= maximo:
            raise HTTPException(
                status.HTTP_409_CONFLICT, f"El equipo ya hizo los {maximo} cambios que permite el reglamento."
            )
        entra, sale = datos.jugador_id, datos.jugador_secundario_id
        if sale not in estado.convocados or sale not in estado.en_cancha:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "El jugador que sale no está en el campo.")
        if entra not in estado.suplentes:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "El jugador que entra debe ser un suplente de la alineación.")
        if entra in estado.ya_entraron or entra in estado.en_cancha:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Ese suplente ya entró al campo.")

    def procesar_efecto_secundario(self, evento: EventoPartidoModel, partido: PartidoModel, revertir: bool = False) -> None:
        """Gol y autogol mueven el marcador; la tarjeta roja deja al jugador sancionado (suspensión automática).
        Con revertir=True deshace esos efectos (al borrar un evento registrado por error). No hace commit."""
        delta = -1 if revertir else 1
        if evento.tipo_evento == TipoEventoEnum.GOL:
            self.marcador_service.registrar_anotacion(partido.id, evento.equipo_id, delta, confirmar=False)
        elif evento.tipo_evento == TipoEventoEnum.AUTOGOL:
            rival = (
                partido.equipo_visitante_id if evento.equipo_id == partido.equipo_local_id else partido.equipo_local_id
            )
            self.marcador_service.registrar_anotacion(partido.id, rival, delta, confirmar=False)
        elif evento.tipo_evento == TipoEventoEnum.TARJETA_ROJA:
            if not revertir:
                self.jugador_repository.actualizar_estado_sancion(evento.jugador_id, True, confirmar=False)
            elif self.repository.contar_tarjetas_rojas(evento.jugador_id, excluir_id=evento.id) == 0:
                self.jugador_repository.actualizar_estado_sancion(evento.jugador_id, False, confirmar=False)

    def eliminar_evento(self, id_partido: int, id_evento: int, arbitro) -> None:
        """Borra un evento registrado por error (solo con el partido En_Juego) y revierte sus efectos."""
        partido, _ = self._partido_en_juego(id_partido, arbitro)
        evento = self.repository.obtener_por_id(id_evento)
        if evento is None or evento.partido_id != partido.id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "El evento solicitado no existe en este partido.")
        self.procesar_efecto_secundario(evento, partido, revertir=True)
        self.repository.eliminar_evento(evento)
        self.repository.confirmar()

    # ---------- consultas ----------
    def obtener_por_partido(self, id_partido: int) -> list[EventoPartidoModel]:
        if self.partido_repository.obtener_por_id(id_partido) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "El partido solicitado no existe.")
        return self.repository.obtener_por_partido(id_partido)

    def obtener_goleadores(self, id_torneo: int, limite: int = 10) -> list[dict]:
        if self.torneo_repository.obtener_por_id(id_torneo) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "El torneo solicitado no existe.")
        return [
            {"jugador_id": id_jugador, "nombre_completo": nombre, "equipo_id": id_equipo, "goles": goles}
            for id_jugador, nombre, id_equipo, goles in self.repository.goleadores(id_torneo, limite)
        ]

    # ---------- auxiliares ----------
    def _partido_en_juego(self, id_partido: int, arbitro):
        partido = self.partido_repository.obtener_por_id(id_partido)
        if partido is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "El partido solicitado no existe.")
        if partido.arbitro_id != arbitro.id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "No eres el árbitro designado de este partido.")
        if partido.estado != EstadoPartidoEnum.EN_JUEGO:
            raise HTTPException(status.HTTP_409_CONFLICT, "El partido no está En_Juego.")
        fase = self.fase_repository.obtener_por_id(partido.fase_id)
        torneo = self.torneo_repository.obtener_por_id(fase.torneo_id)
        if torneo.estado != EstadoTorneoEnum.EN_CURSO:
            raise HTTPException(status.HTTP_409_CONFLICT, "El torneo no está En_Curso.")
        return partido, torneo

    @staticmethod
    def _exigir_en_cancha(id_jugador: int, estado: _EstadoEnCancha) -> None:
        if id_jugador not in estado.en_cancha:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "El jugador no está en el campo en este momento.")
