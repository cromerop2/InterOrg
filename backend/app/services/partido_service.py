"""Reglas de negocio de partidos: programación, cruces de horario y asignación de árbitro."""

from datetime import datetime

from fastapi import HTTPException, status

from app.core.enums import (
    EstadoFaseEnum,
    EstadoInscripcionEnum,
    EstadoPartidoEnum,
    EstadoTorneoEnum,
    RolEnum,
    TipoFormatoEnum,
)
from app.core.permisos import exigir_acceso_a_equipo
from app.core.reglas import DURACION_PARTIDO_MIN, obtener_regla_entera
from app.models.equipo_model import EquipoModel
from app.models.fase_model import FaseModel
from app.models.marcador_model import MarcadorModel
from app.models.partido_model import PartidoModel
from app.models.torneo_model import TorneoModel
from app.repositories.equipo_repository import EquipoRepository
from app.repositories.fase_repository import FaseRepository
from app.repositories.marcador_repository import MarcadorRepository
from app.repositories.partido_repository import PartidoRepository
from app.repositories.tabla_posiciones_repository import TablaPosicionesRepository
from app.repositories.torneo_repository import TorneoRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.partido_schema import PartidoCreate
from app.services.cancha_service import CanchaService

# El día del partido (inicio, eventos, marcador, cierre de acta y W.O.) está en JuegoService.
# Pendiente (Fase 5): generar_programacion_general.


class PartidoService:
    def __init__(
        self,
        repository: PartidoRepository,
        marcador_repository: MarcadorRepository,
        fase_repository: FaseRepository,
        torneo_repository: TorneoRepository,
        equipo_repository: EquipoRepository,
        tabla_repository: TablaPosicionesRepository,
        usuario_repository: UsuarioRepository,
        cancha_service: CanchaService,
    ):
        self.repository = repository
        self.marcador_repository = marcador_repository
        self.fase_repository = fase_repository
        self.torneo_repository = torneo_repository
        self.equipo_repository = equipo_repository
        self.tabla_repository = tabla_repository
        self.usuario_repository = usuario_repository
        self.cancha_service = cancha_service

    # ---------- programación (Administrador) ----------
    def programar_encuentro(self, datos_partido: PartidoCreate) -> PartidoModel:
        """Crea el partido (con su marcador 0-0) tras validar fase, equipos, fecha, cancha y árbitro."""
        fase, torneo = self._fase_y_torneo(datos_partido.fase_id)
        self._exigir_torneo_en_curso(torneo)
        if fase.estado == EstadoFaseEnum.FINALIZADA:
            raise HTTPException(status.HTTP_409_CONFLICT, "La fase ya finalizó.")
        self._exigir_fases_anteriores_finalizadas(fase)

        local = self._equipo_valido(datos_partido.equipo_local_id, torneo)
        visitante = self._equipo_valido(datos_partido.equipo_visitante_id, torneo)
        if fase.tipo_formato == TipoFormatoEnum.GRUPOS:
            self._exigir_mismo_grupo(fase, local, visitante)
        if self.repository.existe_pareja_en_fase(fase.id, local.id, visitante.id):
            raise HTTPException(status.HTTP_409_CONFLICT, "Esos equipos ya se enfrentan en esta fase.")

        duracion = self._duracion(torneo)
        self._validar_fecha_en_torneo(torneo, datos_partido.fecha_hora)
        self._validar_disponibilidad(
            datos_partido.cancha_id, [local.id, visitante.id], datos_partido.arbitro_id,
            datos_partido.fecha_hora, duracion, excluir_id=None,
        )

        partido = self.repository.crear_partido(datos_partido, confirmar=False)
        # Comparten sesión: este commit guarda también el partido.
        self.marcador_repository.crear_marcador_inicial(partido.id)
        return partido

    def reprogramar_encuentro(self, id_partido: int, nueva_fecha: datetime, nueva_cancha: int | None = None) -> PartidoModel:
        """Cambia fecha y/o cancha (lluvia, apagones...). Libera el horario anterior al validar el nuevo."""
        partido = self.obtener_por_id(id_partido)
        if partido.estado not in (EstadoPartidoEnum.PROGRAMADO, EstadoPartidoEnum.SUSPENDIDO):
            raise HTTPException(
                status.HTTP_409_CONFLICT, "Solo se reprograman partidos Programados o Suspendidos."
            )
        _, torneo = self._fase_y_torneo(partido.fase_id)
        self._exigir_torneo_en_curso(torneo)

        cancha = nueva_cancha or partido.cancha_id
        duracion = self._duracion(torneo)
        self._validar_fecha_en_torneo(torneo, nueva_fecha)
        self._validar_disponibilidad(
            cancha, [partido.equipo_local_id, partido.equipo_visitante_id], partido.arbitro_id,
            nueva_fecha, duracion, excluir_id=partido.id,
        )
        return self.repository.reprogramar(partido, nueva_fecha, cancha, EstadoPartidoEnum.PROGRAMADO)

    def suspender_partido(self, id_partido: int) -> PartidoModel:
        """Suspende un partido aún no iniciado; su horario y cancha quedan libres."""
        partido = self.obtener_por_id(id_partido)
        if partido.estado != EstadoPartidoEnum.PROGRAMADO:
            raise HTTPException(status.HTTP_409_CONFLICT, "Solo se suspende un partido Programado.")
        return self.repository.actualizar_estado(partido.id, EstadoPartidoEnum.SUSPENDIDO)

    def asignar_arbitro_partido(self, id_partido: int, id_arbitro: int) -> PartidoModel:
        partido = self.obtener_por_id(id_partido)
        if partido.estado != EstadoPartidoEnum.PROGRAMADO:
            raise HTTPException(status.HTTP_409_CONFLICT, "Solo se asigna árbitro a un partido Programado.")
        _, torneo = self._fase_y_torneo(partido.fase_id)
        self._exigir_torneo_en_curso(torneo)
        self._validar_arbitro(id_arbitro, partido.fecha_hora, self._duracion(torneo), partido.id)
        return self.repository.asignar_arbitro(partido, id_arbitro)

    # ---------- consultas ----------
    def obtener_por_id(self, id_partido: int) -> PartidoModel:
        partido = self.repository.obtener_por_id(id_partido)
        if partido is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "El partido solicitado no existe.")
        return partido

    def listar_por_fase(self, id_fase: int) -> list[PartidoModel]:
        if self.fase_repository.obtener_por_id(id_fase) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "La fase solicitada no existe.")
        return self.repository.listar_por_fase(id_fase)

    def consultar_calendario(self, id_equipo: int, usuario) -> list[PartidoModel]:
        """Partidos de un equipo (local o visitante). Lo ve su entrenador o un Administrador."""
        equipo = self.equipo_repository.obtener_por_id(id_equipo)
        if equipo is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "El equipo solicitado no existe.")
        exigir_acceso_a_equipo(usuario, equipo)
        return self.repository.listar_por_equipo(equipo.id)

    def consultar_asignaciones(self, id_arbitro: int) -> list[PartidoModel]:
        """Partidos en los que el administrador designó a este árbitro."""
        return self.repository.listar_por_arbitro(id_arbitro)

    def obtener_marcador(self, id_partido: int) -> MarcadorModel:
        self.obtener_por_id(id_partido)
        return self.marcador_repository.obtener_por_partido(id_partido)

    # ---------- auxiliares ----------
    def _fase_y_torneo(self, id_fase: int) -> tuple[FaseModel, TorneoModel]:
        fase = self.fase_repository.obtener_por_id(id_fase)
        if fase is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "La fase indicada no existe.")
        return fase, self.torneo_repository.obtener_por_id(fase.torneo_id)

    @staticmethod
    def _exigir_torneo_en_curso(torneo: TorneoModel) -> None:
        if torneo.estado != EstadoTorneoEnum.EN_CURSO:
            raise HTTPException(status.HTTP_409_CONFLICT, "El torneo no está En_Curso.")

    def _exigir_fases_anteriores_finalizadas(self, fase: FaseModel) -> None:
        """Una fase solo se programa cuando las anteriores del torneo (creadas antes) ya finalizaron."""
        for anterior in self.fase_repository.obtener_por_torneo(fase.torneo_id):
            if anterior.id < fase.id and anterior.estado != EstadoFaseEnum.FINALIZADA:
                raise HTTPException(
                    status.HTTP_409_CONFLICT, f"La fase anterior '{anterior.nombre}' aún no finaliza."
                )

    def _equipo_valido(self, id_equipo: int, torneo: TorneoModel) -> EquipoModel:
        equipo = self.equipo_repository.obtener_por_id(id_equipo)
        if equipo is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"El equipo {id_equipo} no existe.")
        if equipo.torneo_id != torneo.id or equipo.estado_inscripcion != EstadoInscripcionEnum.HABILITADO:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"El equipo {equipo.nombre} no está Habilitado en este torneo.",
            )
        return equipo

    def _exigir_mismo_grupo(self, fase: FaseModel, local: EquipoModel, visitante: EquipoModel) -> None:
        tabla_local = self.tabla_repository.obtener_por_fase_y_equipo(fase.id, local.id)
        tabla_visitante = self.tabla_repository.obtener_por_fase_y_equipo(fase.id, visitante.id)
        if tabla_local is None or tabla_visitante is None or tabla_local.id != tabla_visitante.id:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "En una fase de grupos, ambos equipos deben pertenecer al mismo grupo.",
            )

    @staticmethod
    def _duracion(torneo: TorneoModel) -> int:
        return obtener_regla_entera(torneo, "duracion_partido_min", DURACION_PARTIDO_MIN)

    @staticmethod
    def _validar_fecha_en_torneo(torneo: TorneoModel, fecha_hora: datetime) -> None:
        if not torneo.fecha_inicio <= fecha_hora.date() <= torneo.fecha_fin:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"La fecha debe estar entre {torneo.fecha_inicio} y {torneo.fecha_fin}, las fechas del torneo.",
            )

    def _validar_disponibilidad(self, id_cancha, ids_equipos, id_arbitro, inicio, duracion, excluir_id) -> None:
        cancha = self.cancha_service.obtener_por_id(id_cancha)  # 404 si no existe
        if not cancha.estado_activo:
            raise HTTPException(status.HTTP_409_CONFLICT, "La cancha está inhabilitada.")
        if not self.cancha_service.verificar_disponibilidad(id_cancha, inicio, duracion, excluir_id):
            raise HTTPException(status.HTTP_409_CONFLICT, "La cancha ya está ocupada en ese horario.")
        if self.repository.cruce_de_equipos(ids_equipos, inicio, duracion, excluir_id):
            raise HTTPException(
                status.HTTP_409_CONFLICT, "Uno de los equipos ya tiene un partido en ese horario."
            )
        if id_arbitro is not None:
            self._validar_arbitro(id_arbitro, inicio, duracion, excluir_id)

    def _validar_arbitro(self, id_arbitro: int, inicio: datetime, duracion: int, excluir_id: int | None) -> None:
        arbitro = self.usuario_repository.obtener_por_id(id_arbitro)
        if arbitro is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "El árbitro indicado no existe.")
        if arbitro.rol != RolEnum.ARBITRO or not arbitro.estado_activo:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "El usuario indicado no es un árbitro activo.")
        if self.repository.cruce_de_arbitro(id_arbitro, inicio, duracion, excluir_id):
            raise HTTPException(status.HTTP_409_CONFLICT, "El árbitro ya tiene un partido en ese horario.")
