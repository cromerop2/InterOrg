"""Reglas de negocio del marcador: goles, penales y resultado final."""

from fastapi import HTTPException, status

from app.core.enums import TipoFormatoEnum
from app.models.marcador_model import MarcadorModel
from app.repositories.fase_repository import FaseRepository
from app.repositories.marcador_repository import MarcadorRepository
from app.repositories.partido_repository import PartidoRepository


class MarcadorService:
    def __init__(
        self,
        repository: MarcadorRepository,
        partido_repository: PartidoRepository,
        fase_repository: FaseRepository,
    ):
        self.repository = repository
        self.partido_repository = partido_repository
        self.fase_repository = fase_repository

    def obtener_por_partido(self, id_partido: int) -> MarcadorModel:
        marcador = self.repository.obtener_por_partido(id_partido)
        if marcador is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "El partido no tiene marcador.")
        return marcador

    def actualizar_goles(
        self,
        id_partido: int,
        goles_local: int,
        goles_visitante: int,
        penales_local: int | None = None,
        penales_visitante: int | None = None,
        confirmar: bool = True,
    ) -> MarcadorModel:
        """Sobrescribe el resultado mientras el acta siga abierta."""
        marcador = self._editable(id_partido)
        return self.repository.actualizar_goles(
            marcador, goles_local, goles_visitante, penales_local, penales_visitante, confirmar
        )

    def registrar_anotacion(
        self, id_partido: int, id_equipo_anotador: int, delta: int = 1, confirmar: bool = True
    ) -> MarcadorModel:
        """Suma (o resta, con delta=-1) un gol al equipo que anota, según sea local o visitante."""
        marcador = self._editable(id_partido)
        partido = self.partido_repository.obtener_por_id(id_partido)
        goles_local, goles_visitante = marcador.goles_local, marcador.goles_visitante
        if id_equipo_anotador == partido.equipo_local_id:
            goles_local = max(0, goles_local + delta)
        elif id_equipo_anotador == partido.equipo_visitante_id:
            goles_visitante = max(0, goles_visitante + delta)
        else:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Ese equipo no juega este partido.")
        return self.repository.actualizar_goles(
            marcador,
            goles_local,
            goles_visitante,
            marcador.goles_penales_local,
            marcador.goles_penales_visitante,
            confirmar,
        )

    def validar_necesidad_desempate(self, id_partido: int) -> bool:
        """True si es una eliminatoria directa y el partido va empatado: hay que definir por penales."""
        partido = self.partido_repository.obtener_por_id(id_partido)
        fase = self.fase_repository.obtener_por_id(partido.fase_id)
        marcador = self.obtener_por_partido(id_partido)
        return (
            fase.tipo_formato == TipoFormatoEnum.ELIMINATORIA_DIRECTA
            and marcador.goles_local == marcador.goles_visitante
        )

    def corregir_resultado(
        self,
        id_partido: int,
        goles_local: int,
        goles_visitante: int,
        penales_local: int | None = None,
        penales_visitante: int | None = None,
        confirmar: bool = True,
    ) -> MarcadorModel:
        """Cambia el resultado de un acta YA cerrada. Solo lo usa la corrección auditada del Administrador."""
        marcador = self.obtener_por_partido(id_partido)
        return self.repository.actualizar_goles(
            marcador, goles_local, goles_visitante, penales_local, penales_visitante, confirmar
        )

    def fijar_resultado_final(self, id_partido: int, confirmar: bool = True) -> MarcadorModel:
        marcador = self._editable(id_partido)
        return self.repository.fijar_resultado_final(marcador, confirmar)

    def _editable(self, id_partido: int) -> MarcadorModel:
        marcador = self.obtener_por_partido(id_partido)
        if marcador.es_resultado_final:
            raise HTTPException(status.HTTP_409_CONFLICT, "El acta ya está cerrada: el marcador no se modifica.")
        return marcador
