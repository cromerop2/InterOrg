"""Reglas de negocio de torneos."""

from fastapi import HTTPException, status

from app.core.enums import EstadoInscripcionEnum, EstadoTorneoEnum
from app.core.reglas import MINIMO_EQUIPOS, obtener_regla_entera
from app.models.torneo_model import TorneoModel
from app.repositories.equipo_repository import EquipoRepository
from app.repositories.torneo_repository import TorneoRepository
from app.schemas.torneo_schema import TorneoCreate, TorneoUpdate


class TorneoService:
    def __init__(self, repository: TorneoRepository, equipo_repository: EquipoRepository):
        self.repository = repository
        self.equipo_repository = equipo_repository

    def crear_torneo(self, datos_torneo: TorneoCreate) -> TorneoModel:
        return self.repository.crear_torneo(datos_torneo)

    def obtener_por_id(self, id_torneo: int) -> TorneoModel:
        torneo = self.repository.obtener_por_id(id_torneo)
        if torneo is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "El torneo solicitado no existe.")
        return torneo

    def obtener_todos(self, estado_filtro: EstadoTorneoEnum | None = None) -> list[TorneoModel]:
        return self.repository.obtener_todos(estado_filtro)

    def actualizar_detalles(self, id_torneo: int, datos: TorneoUpdate) -> TorneoModel:
        """Solo se editan los datos mientras el torneo está en "Inscripciones"."""
        torneo = self.obtener_por_id(id_torneo)
        if torneo.estado != EstadoTorneoEnum.INSCRIPCIONES:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "Solo se pueden modificar los datos de un torneo en estado Inscripciones.",
            )
        # El orden de las fechas se valida con lo que ya está guardado, no solo con lo enviado.
        cambios = datos.model_dump(exclude_unset=True)
        inicio = cambios.get("fecha_inicio", torneo.fecha_inicio)
        fin = cambios.get("fecha_fin", torneo.fecha_fin)
        if fin < inicio:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "fecha_fin no puede ser anterior a fecha_inicio.",
            )
        return self.repository.actualizar_detalles(id_torneo, datos)

    def iniciar_torneo(self, id_torneo: int) -> TorneoModel:
        """Pasa el torneo a "En_Curso" si hay suficientes equipos Habilitados, y bloquea las plantillas."""
        torneo = self.obtener_por_id(id_torneo)
        if torneo.estado != EstadoTorneoEnum.INSCRIPCIONES:
            raise HTTPException(
                status.HTTP_409_CONFLICT, "Solo se puede iniciar un torneo que está en Inscripciones."
            )
        habilitados = self.equipo_repository.obtener_por_torneo(id_torneo, EstadoInscripcionEnum.HABILITADO)
        minimo = obtener_regla_entera(torneo, "min_equipos", MINIMO_EQUIPOS)
        if len(habilitados) < minimo:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"Se necesitan al menos {minimo} equipos Habilitados y hay {len(habilitados)}.",
            )
        self.equipo_repository.bloquear_plantillas_de_torneo(id_torneo, confirmar=False)
        # Comparten sesión: este commit guarda también el bloqueo de las plantillas.
        return self.repository.actualizar_estado(id_torneo, EstadoTorneoEnum.EN_CURSO)

    def finalizar_torneo(self, id_torneo: int) -> TorneoModel:
        """Cierra el torneo. Solo es posible desde "En_Curso"."""
        torneo = self.obtener_por_id(id_torneo)
        if torneo.estado != EstadoTorneoEnum.EN_CURSO:
            raise HTTPException(
                status.HTTP_409_CONFLICT, "Solo se puede finalizar un torneo que está En_Curso."
            )
        return self.repository.actualizar_estado(id_torneo, EstadoTorneoEnum.FINALIZADO)

    def cancelar_torneo(self, id_torneo: int) -> TorneoModel:
        """Cancela un torneo en "Inscripciones" o "En_Curso"."""
        torneo = self.obtener_por_id(id_torneo)
        if torneo.estado not in (EstadoTorneoEnum.INSCRIPCIONES, EstadoTorneoEnum.EN_CURSO):
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "Solo se puede cancelar un torneo en Inscripciones o En_Curso.",
            )
        return self.repository.actualizar_estado(id_torneo, EstadoTorneoEnum.CANCELADO)
