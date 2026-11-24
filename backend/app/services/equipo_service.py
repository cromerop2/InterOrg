"""Reglas de negocio de equipos: inscripción, habilitación y solvencia."""

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.core.enums import EstadoInscripcionEnum, EstadoPagoEnum, EstadoTorneoEnum
from app.core.permisos import exigir_acceso_a_equipo
from app.core.reglas import MINIMO_JUGADORES, obtener_regla_entera
from app.models.equipo_model import EquipoModel
from app.models.fila_posicion_model import FilaPosicionModel
from app.models.torneo_model import TorneoModel
from app.repositories.colegio_repository import ColegioRepository
from app.repositories.equipo_repository import EquipoRepository
from app.repositories.fila_posicion_repository import FilaPosicionRepository
from app.repositories.jugador_repository import JugadorRepository
from app.repositories.pago_repository import PagoRepository
from app.repositories.torneo_repository import TorneoRepository
from app.schemas.equipo_schema import EquipoCreate


class EquipoService:
    def __init__(
        self,
        repository: EquipoRepository,
        torneo_repository: TorneoRepository,
        colegio_repository: ColegioRepository,
        jugador_repository: JugadorRepository,
        pago_repository: PagoRepository,
        fila_repository: FilaPosicionRepository,
    ):
        self.repository = repository
        self.torneo_repository = torneo_repository
        self.colegio_repository = colegio_repository
        self.jugador_repository = jugador_repository
        self.pago_repository = pago_repository
        self.fila_repository = fila_repository

    # ---------- inscripción ----------
    def registrar_equipo(self, datos_equipo: EquipoCreate, entrenador) -> EquipoModel:
        """Inscribe un equipo del entrenador autenticado en un torneo (estado inicial "Preinscrito")."""
        torneo = self.torneo_repository.obtener_por_id(datos_equipo.torneo_id)
        if torneo is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "El torneo indicado no existe.")
        if torneo.estado != EstadoTorneoEnum.INSCRIPCIONES:
            raise HTTPException(
                status.HTTP_409_CONFLICT, "El torneo no está recibiendo inscripciones."
            )

        colegio = self.colegio_repository.obtener_por_id(datos_equipo.colegio_id)
        if colegio is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "El colegio indicado no existe.")
        if not colegio.estado_activo:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "El colegio indicado está inactivo.")

        # Un entrenador vinculado a un colegio solo inscribe equipos de ese colegio.
        colegio_del_entrenador = getattr(entrenador, "colegio_id", None)
        if colegio_del_entrenador is not None and colegio_del_entrenador != datos_equipo.colegio_id:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, "Tu cuenta está vinculada a otro colegio."
            )

        if self.repository.obtener_por_nombre(datos_equipo.torneo_id, datos_equipo.nombre):
            raise HTTPException(
                status.HTTP_409_CONFLICT, "Ya existe un equipo con ese nombre en el torneo."
            )
        try:
            return self.repository.crear_equipo(datos_equipo, entrenador.id)
        except IntegrityError:
            raise HTTPException(
                status.HTTP_409_CONFLICT, "Ya existe un equipo con ese nombre en el torneo."
            )

    # ---------- consultas ----------
    def obtener_equipo(self, id_equipo: int) -> EquipoModel:
        """Busca el equipo sin comprobar permisos (uso interno entre servicios)."""
        equipo = self.repository.obtener_por_id(id_equipo)
        if equipo is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "El equipo solicitado no existe.")
        return equipo

    def obtener_por_id(self, id_equipo: int, usuario) -> EquipoModel:
        equipo = self.obtener_equipo(id_equipo)
        exigir_acceso_a_equipo(usuario, equipo)
        return equipo

    def obtener_por_torneo(self, id_torneo: int) -> list[EquipoModel]:
        if self.torneo_repository.obtener_por_id(id_torneo) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "El torneo solicitado no existe.")
        return self.repository.obtener_por_torneo(id_torneo)

    def obtener_habilitados_publicos(self, id_torneo: int) -> list[EquipoModel]:
        """Equipos Habilitados del torneo (consulta pública)."""
        if self.torneo_repository.obtener_por_id(id_torneo) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "El torneo solicitado no existe.")
        return self.repository.obtener_por_torneo(id_torneo, EstadoInscripcionEnum.HABILITADO)

    def obtener_mis_equipos(self, entrenador) -> list[EquipoModel]:
        return self.repository.obtener_por_entrenador(entrenador.id)

    def obtener_equipos_inscritos(self, id_colegio: int) -> list[EquipoModel]:
        """Todos los equipos de un colegio, en cualquier torneo."""
        if self.colegio_repository.obtener_por_id(id_colegio) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "El colegio solicitado no existe.")
        return self.repository.obtener_por_colegio(id_colegio)

    def obtener_estadisticas_actuales(self, id_equipo: int, usuario) -> list[FilaPosicionModel]:
        """Puntos, goles y rendimiento del equipo: una fila por cada grupo en que ha jugado."""
        equipo = self.obtener_equipo(id_equipo)
        exigir_acceso_a_equipo(usuario, equipo)
        return self.fila_repository.obtener_por_equipo(equipo.id)

    # ---------- reglas ----------
    def validar_minimo_jugadores(self, id_equipo: int) -> bool:
        """True si el equipo tiene al menos el mínimo de jugadores activos que exige el torneo."""
        equipo = self.obtener_equipo(id_equipo)
        torneo = self.torneo_repository.obtener_por_id(equipo.torneo_id)
        return self.jugador_repository.contar_activos(id_equipo) >= self._minimo(torneo)

    def bloquear_plantilla(self, id_equipo: int) -> EquipoModel:
        self.obtener_equipo(id_equipo)
        return self.repository.bloquear_plantilla(id_equipo)

    def verificar_solvencia(self, id_equipo: int) -> bool:
        """True si el equipo tiene un pago Aprobado."""
        self.obtener_equipo(id_equipo)
        return self.pago_repository.existe_aprobado(id_equipo)

    def auditar_inscripcion_equipo(self, id_equipo: int, id_pago: int) -> EquipoModel:
        """Aprueba el pago y habilita el equipo, si el pago es válido y la plantilla está completa.

        Se guardan juntos el pago "Aprobado" y el equipo "Habilitado": o ambos o ninguno.
        """
        equipo = self.obtener_equipo(id_equipo)
        torneo = self.torneo_repository.obtener_por_id(equipo.torneo_id)

        if torneo.estado != EstadoTorneoEnum.INSCRIPCIONES:
            raise HTTPException(
                status.HTTP_409_CONFLICT, "Solo se habilitan equipos mientras el torneo está en Inscripciones."
            )
        if equipo.estado_inscripcion in (
            EstadoInscripcionEnum.HABILITADO,
            EstadoInscripcionEnum.DESCALIFICADO,
        ):
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                f"El equipo ya está {equipo.estado_inscripcion.value}.",
            )

        pago = self.pago_repository.obtener_por_id(id_pago)
        if pago is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "El pago indicado no existe.")
        if pago.equipo_id != equipo.id:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "El pago indicado no pertenece a este equipo."
            )
        if pago.estado != EstadoPagoEnum.PENDIENTE:
            raise HTTPException(status.HTTP_409_CONFLICT, "Ese pago ya fue revisado.")

        minimo = self._minimo(torneo)
        activos = self.jugador_repository.contar_activos(equipo.id)
        if activos < minimo:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"Plantilla incompleta: tiene {activos} jugadores y el torneo exige {minimo}.",
            )

        self.pago_repository.actualizar_estado(pago.id, EstadoPagoEnum.APROBADO, confirmar=False)
        # Comparten sesión: este commit guarda también el pago aprobado.
        return self.repository.actualizar_estado(equipo.id, EstadoInscripcionEnum.HABILITADO)

    def descalificar(self, id_equipo: int) -> EquipoModel:
        equipo = self.obtener_equipo(id_equipo)
        if equipo.estado_inscripcion == EstadoInscripcionEnum.DESCALIFICADO:
            raise HTTPException(status.HTTP_409_CONFLICT, "El equipo ya está Descalificado.")
        return self.repository.actualizar_estado(equipo.id, EstadoInscripcionEnum.DESCALIFICADO)

    @staticmethod
    def _minimo(torneo: TorneoModel) -> int:
        return obtener_regla_entera(torneo, "min_jugadores", MINIMO_JUGADORES)
