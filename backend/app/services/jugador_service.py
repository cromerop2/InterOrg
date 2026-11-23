"""Reglas de negocio de jugadores: plantilla, edad, elegibilidad y transferencias."""

import re
from datetime import date

from fastapi import HTTPException, status

from app.core.enums import EstadoInscripcionEnum, EstadoTorneoEnum
from app.core.permisos import exigir_acceso_a_equipo
from app.core.reglas import MAXIMO_JUGADORES, MINIMO_JUGADORES, obtener_regla_entera, permite_transferencias
from app.models.equipo_model import EquipoModel
from app.models.jugador_model import JugadorModel
from app.repositories.equipo_repository import EquipoRepository
from app.repositories.jugador_repository import JugadorRepository
from app.repositories.torneo_repository import TorneoRepository
from app.schemas.jugador_schema import JugadorCreate

_CATEGORIA_SUB = re.compile(r"^\s*sub[-\s]?(\d{1,2})\s*$", re.IGNORECASE)


class JugadorService:
    def __init__(
        self,
        repository: JugadorRepository,
        equipo_repository: EquipoRepository,
        torneo_repository: TorneoRepository,
    ):
        self.repository = repository
        self.equipo_repository = equipo_repository
        self.torneo_repository = torneo_repository

    # ---------- plantilla (Entrenador) ----------
    def agregar_jugador_plantilla(self, id_equipo: int, datos_jugador: JugadorCreate, entrenador) -> JugadorModel:
        equipo = self._equipo(id_equipo)
        exigir_acceso_a_equipo(entrenador, equipo, solo_dueno=True)
        self._exigir_plantilla_modificable(equipo)

        torneo = self.torneo_repository.obtener_por_id(equipo.torneo_id)
        maximo = obtener_regla_entera(torneo, "max_jugadores", MAXIMO_JUGADORES)
        if self.repository.contar_activos(equipo.id) >= maximo:
            raise HTTPException(
                status.HTTP_409_CONFLICT, f"La plantilla ya alcanzó el máximo de {maximo} jugadores."
            )
        if not self.validar_requisitos_edad(datos_jugador.fecha_nacimiento, torneo.categoria, torneo.fecha_inicio):
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"El jugador supera la edad máxima de la categoría {torneo.categoria}.",
            )
        if self.repository.obtener_por_identificacion_en_torneo(datos_jugador.identificacion, torneo.id):
            raise HTTPException(
                status.HTTP_409_CONFLICT, "Ese documento ya está inscrito como jugador activo en el torneo."
            )
        return self.repository.crear_jugador(equipo.id, datos_jugador)

    def dar_de_baja_jugador(self, id_jugador: int, entrenador) -> JugadorModel:
        """Desactiva al jugador mientras la plantilla siga abierta."""
        jugador = self._jugador(id_jugador)
        equipo = self._equipo(jugador.equipo_id)
        exigir_acceso_a_equipo(entrenador, equipo, solo_dueno=True)
        self._exigir_plantilla_modificable(equipo)
        if not jugador.estado_activo:
            raise HTTPException(status.HTTP_409_CONFLICT, "El jugador ya está dado de baja.")

        # Un equipo ya Habilitado no puede quedar por debajo del mínimo.
        if equipo.estado_inscripcion == EstadoInscripcionEnum.HABILITADO:
            torneo = self.torneo_repository.obtener_por_id(equipo.torneo_id)
            minimo = obtener_regla_entera(torneo, "min_jugadores", MINIMO_JUGADORES)
            if self.repository.contar_activos(equipo.id) - 1 < minimo:
                raise HTTPException(
                    status.HTTP_409_CONFLICT,
                    f"El equipo está Habilitado y quedaría por debajo del mínimo de {minimo} jugadores.",
                )
        return self.repository.dar_de_baja(jugador.id)

    # ---------- consultas ----------
    def obtener_por_id(self, id_jugador: int, usuario) -> JugadorModel:
        jugador = self._jugador(id_jugador)
        exigir_acceso_a_equipo(usuario, self._equipo(jugador.equipo_id))
        return jugador

    def obtener_por_equipo(self, id_equipo: int, usuario, solo_activos: bool = True) -> list[JugadorModel]:
        equipo = self._equipo(id_equipo)
        exigir_acceso_a_equipo(usuario, equipo)
        return self.repository.obtener_por_equipo(equipo.id, solo_activos)

    # ---------- reglas ----------
    @staticmethod
    def validar_requisitos_edad(
        fecha_nacimiento: date, categoria_torneo: str, fecha_referencia: date | None = None
    ) -> bool:
        """True si el jugador cumple el límite de edad de la categoría.

        "Sub-N" significa no tener más de N años cumplidos en la fecha de referencia (por defecto, hoy;
        al inscribir se usa la fecha de inicio del torneo). Las categorías sin formato "Sub-N"
        (ej. "Femenino Libre") no tienen límite de edad.
        """
        coincidencia = _CATEGORIA_SUB.match(categoria_torneo or "")
        if coincidencia is None:
            return True
        referencia = fecha_referencia or date.today()
        edad = referencia.year - fecha_nacimiento.year - (
            (referencia.month, referencia.day) < (fecha_nacimiento.month, fecha_nacimiento.day)
        )
        return edad <= int(coincidencia.group(1))

    def verificar_elegibilidad(self, id_jugador: int) -> bool:
        """True si el jugador está activo y no sancionado (lo usa la Alineación en la Fase 4)."""
        jugador = self._jugador(id_jugador)
        return bool(jugador.estado_activo) and not jugador.sancionado

    # ---------- Administrador ----------
    def actualizar_estado_sancion(self, id_jugador: int, sancionado: bool) -> JugadorModel:
        self._jugador(id_jugador)
        return self.repository.actualizar_estado_sancion(id_jugador, sancionado)

    def aplicar_sancion_disciplinaria(self, id_jugador: int, fechas_suspension: int) -> JugadorModel:
        """Suspende al jugador por un número de fechas: no podrá estar en las alineaciones de los próximos
        partidos de su equipo. Cada partido cerrado del equipo descuenta una fecha."""
        self._jugador(id_jugador)
        return self.repository.aplicar_sancion(id_jugador, fechas_suspension)

    def transferir_equipo(self, id_jugador: int, nuevo_equipo_id: int) -> JugadorModel:
        """Pasa al jugador a otro equipo del mismo torneo, solo si las reglas del torneo lo permiten."""
        jugador = self._jugador(id_jugador)
        if not jugador.estado_activo:
            raise HTTPException(status.HTTP_409_CONFLICT, "El jugador está dado de baja.")
        origen = self._equipo(jugador.equipo_id)
        destino = self.equipo_repository.obtener_por_id(nuevo_equipo_id)
        if destino is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "El equipo de destino no existe.")
        if destino.id == origen.id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "El jugador ya pertenece a ese equipo.")
        if destino.torneo_id != origen.torneo_id:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "Solo se puede transferir entre equipos del mismo torneo."
            )

        torneo = self.torneo_repository.obtener_por_id(origen.torneo_id)
        if not permite_transferencias(torneo):
            raise HTTPException(
                status.HTTP_409_CONFLICT, "Las reglas del torneo no permiten transferencias."
            )
        if torneo.estado in (EstadoTorneoEnum.FINALIZADO, EstadoTorneoEnum.CANCELADO):
            raise HTTPException(status.HTTP_409_CONFLICT, "El torneo ya terminó.")
        if destino.estado_inscripcion == EstadoInscripcionEnum.DESCALIFICADO:
            raise HTTPException(status.HTTP_409_CONFLICT, "El equipo de destino está Descalificado.")
        maximo = obtener_regla_entera(torneo, "max_jugadores", MAXIMO_JUGADORES)
        if self.repository.contar_activos(destino.id) >= maximo:
            raise HTTPException(
                status.HTTP_409_CONFLICT, f"El equipo de destino ya tiene el máximo de {maximo} jugadores."
            )
        return self.repository.mover_a_equipo(jugador.id, destino.id)

    # ---------- auxiliares ----------
    def _jugador(self, id_jugador: int) -> JugadorModel:
        jugador = self.repository.obtener_por_id(id_jugador)
        if jugador is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "El jugador solicitado no existe.")
        return jugador

    def _equipo(self, id_equipo: int) -> EquipoModel:
        equipo = self.equipo_repository.obtener_por_id(id_equipo)
        if equipo is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "El equipo solicitado no existe.")
        return equipo

    @staticmethod
    def _exigir_plantilla_modificable(equipo: EquipoModel) -> None:
        if equipo.plantilla_bloqueada:
            raise HTTPException(
                status.HTTP_409_CONFLICT, "La plantilla está bloqueada: el torneo ya inició."
            )
        if equipo.estado_inscripcion == EstadoInscripcionEnum.DESCALIFICADO:
            raise HTTPException(status.HTTP_409_CONFLICT, "El equipo está Descalificado.")
