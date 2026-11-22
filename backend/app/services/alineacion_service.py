"""Reglas de negocio de alineaciones: la planilla que cada entrenador entrega antes del partido."""

from fastapi import HTTPException, status

from app.core.enums import EstadoPartidoEnum, EstadoTorneoEnum
from app.core.permisos import exigir_acceso_a_equipo
from app.core.reglas import MAXIMO_SUPLENTES, TITULARES, obtener_regla_entera
from app.models.alineacion_model import AlineacionModel
from app.repositories.alineacion_repository import AlineacionRepository
from app.repositories.equipo_repository import EquipoRepository
from app.repositories.fase_repository import FaseRepository
from app.repositories.jugador_repository import JugadorRepository
from app.repositories.partido_repository import PartidoRepository
from app.repositories.torneo_repository import TorneoRepository
from app.schemas.alineacion_schema import JugadorConvocado


class AlineacionService:
    def __init__(
        self,
        repository: AlineacionRepository,
        partido_repository: PartidoRepository,
        equipo_repository: EquipoRepository,
        jugador_repository: JugadorRepository,
        fase_repository: FaseRepository,
        torneo_repository: TorneoRepository,
    ):
        self.repository = repository
        self.partido_repository = partido_repository
        self.equipo_repository = equipo_repository
        self.jugador_repository = jugador_repository
        self.fase_repository = fase_repository
        self.torneo_repository = torneo_repository

    def enviar_planilla_oficial(
        self, id_partido: int, id_equipo: int, jugadores: list[JugadorConvocado], entrenador
    ) -> list[AlineacionModel]:
        """Guarda la planilla del equipo (o la reemplaza si ya había una) tras validarla por completo.

        Si un solo jugador no es elegible, no se guarda nada.
        """
        partido = self.partido_repository.obtener_por_id(id_partido)
        if partido is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "El partido solicitado no existe.")
        equipo = self.equipo_repository.obtener_por_id(id_equipo)
        if equipo is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "El equipo solicitado no existe.")
        exigir_acceso_a_equipo(entrenador, equipo, solo_dueno=True)

        if equipo.id not in (partido.equipo_local_id, partido.equipo_visitante_id):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Ese equipo no juega este partido.")
        if partido.estado != EstadoPartidoEnum.PROGRAMADO:
            raise HTTPException(
                status.HTTP_409_CONFLICT, "La planilla solo se envía o se rehace con el partido Programado."
            )
        fase = self.fase_repository.obtener_por_id(partido.fase_id)
        torneo = self.torneo_repository.obtener_por_id(fase.torneo_id)
        if torneo.estado != EstadoTorneoEnum.EN_CURSO:
            raise HTTPException(status.HTTP_409_CONFLICT, "El torneo no está En_Curso.")

        self.validar_reglas_plantilla(jugadores, torneo)
        self.auditar_elegibilidad_jugadores(equipo.id, [j.jugador_id for j in jugadores])

        filas = [
            {
                "partido_id": partido.id,
                "equipo_id": equipo.id,
                "jugador_id": j.jugador_id,
                "es_titular": j.es_titular,
                "numero_camiseta": j.numero_camiseta,
            }
            for j in jugadores
        ]
        # Borrado y alta se guardan en un solo commit: nunca queda una planilla a medias.
        self.repository.eliminar_planilla(partido.id, equipo.id, confirmar=False)
        return self.repository.guardar_lista_jugadores(filas)

    @staticmethod
    def validar_reglas_plantilla(jugadores: list[JugadorConvocado], torneo) -> None:
        """Exige la cantidad exacta de titulares, no pasar el máximo de suplentes y no repetir jugadores
        ni números de camiseta. Lanza 400 si algo falla."""
        titulares_exigidos = obtener_regla_entera(torneo, "titulares", TITULARES)
        maximo_suplentes = obtener_regla_entera(torneo, "max_suplentes", MAXIMO_SUPLENTES)

        ids = [j.jugador_id for j in jugadores]
        if len(ids) != len(set(ids)):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "La planilla repite jugadores.")
        numeros = [j.numero_camiseta for j in jugadores if j.numero_camiseta is not None]
        if len(numeros) != len(set(numeros)):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "La planilla repite números de camiseta.")

        titulares = sum(1 for j in jugadores if j.es_titular)
        suplentes = len(jugadores) - titulares
        if titulares != titulares_exigidos:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"Se exigen exactamente {titulares_exigidos} titulares y se enviaron {titulares}.",
            )
        if suplentes > maximo_suplentes:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"Se permiten máximo {maximo_suplentes} suplentes y se enviaron {suplentes}.",
            )

    def auditar_elegibilidad_jugadores(self, id_equipo: int, ids_jugadores: list[int]) -> None:
        """Cada jugador debe ser de ese equipo, estar activo y no sancionado; si uno falla, se rechaza todo."""
        for id_jugador in ids_jugadores:
            jugador = self.jugador_repository.obtener_por_id(id_jugador)
            if jugador is None or jugador.equipo_id != id_equipo:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST, f"El jugador {id_jugador} no pertenece a este equipo."
                )
            if not jugador.estado_activo or jugador.sancionado:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST, f"El jugador {jugador.nombre_completo} está inhabilitado."
                )

    def validar_alineaciones(self, id_partido: int) -> bool:
        """True si los dos equipos ya enviaron su planilla (si falta una, el administrador puede decretar W.O.)."""
        partido = self.partido_repository.obtener_por_id(id_partido)
        if partido is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "El partido solicitado no existe.")
        return all(
            self.repository.obtener_por_partido_y_equipo(partido.id, id_equipo)
            for id_equipo in (partido.equipo_local_id, partido.equipo_visitante_id)
        )

    def obtener_por_partido(self, id_partido: int) -> list[AlineacionModel]:
        if self.partido_repository.obtener_por_id(id_partido) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "El partido solicitado no existe.")
        return self.repository.obtener_por_partido(id_partido)
