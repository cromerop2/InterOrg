"""Reglas de negocio de grupos y tablas de posiciones."""

from fastapi import HTTPException, status

from app.core.enums import EstadoFaseEnum, EstadoInscripcionEnum, EstadoTorneoEnum, TipoFormatoEnum
from app.models.fila_posicion_model import FilaPosicionModel
from app.models.tabla_posiciones_model import TablaPosicionesModel
from app.repositories.equipo_repository import EquipoRepository
from app.repositories.fase_repository import FaseRepository
from app.repositories.fila_posicion_repository import FilaPosicionRepository
from app.repositories.tabla_posiciones_repository import TablaPosicionesRepository
from app.repositories.torneo_repository import TorneoRepository
from app.schemas.tabla_posiciones_schema import GruposConfiguracion

# Pendiente (Fase 4B): desempate por enfrentamiento directo, actualización con cada resultado y cierre de grupo.


class TablaPosicionesService:
    def __init__(
        self,
        repository: TablaPosicionesRepository,
        fila_repository: FilaPosicionRepository,
        fase_repository: FaseRepository,
        torneo_repository: TorneoRepository,
        equipo_repository: EquipoRepository,
    ):
        self.repository = repository
        self.fila_repository = fila_repository
        self.fase_repository = fase_repository
        self.torneo_repository = torneo_repository
        self.equipo_repository = equipo_repository

    def inicializar_grupos(self, id_fase: int, distribucion: GruposConfiguracion) -> list[TablaPosicionesModel]:
        """Crea los grupos de una fase con sus equipos y las filas en ceros, todo en una transacción."""
        fase = self.fase_repository.obtener_por_id(id_fase)
        if fase is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "La fase solicitada no existe.")
        if fase.tipo_formato != TipoFormatoEnum.GRUPOS:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Solo las fases de formato Grupos tienen grupos.")
        torneo = self.torneo_repository.obtener_por_id(fase.torneo_id)
        if torneo.estado != EstadoTorneoEnum.EN_CURSO:
            raise HTTPException(status.HTTP_409_CONFLICT, "El torneo no está En_Curso.")
        if fase.estado != EstadoFaseEnum.PROGRAMADA:
            raise HTTPException(status.HTTP_409_CONFLICT, "La fase ya comenzó.")

        for equipos in distribucion.grupos.values():
            for id_equipo in equipos:
                equipo = self.equipo_repository.obtener_por_id(id_equipo)
                if (
                    equipo is None
                    or equipo.torneo_id != torneo.id
                    or equipo.estado_inscripcion != EstadoInscripcionEnum.HABILITADO
                ):
                    raise HTTPException(
                        status.HTTP_400_BAD_REQUEST,
                        f"El equipo {id_equipo} no existe o no está Habilitado en este torneo.",
                    )
        if self.repository.obtener_por_fase(fase.id):
            raise HTTPException(status.HTTP_409_CONFLICT, "La fase ya tiene grupos definidos.")

        tablas = []
        for nombre, equipos in distribucion.grupos.items():
            tabla = self.repository.crear_tabla(fase.id, nombre.strip(), confirmar=False)
            for id_equipo in equipos:
                self.fila_repository.crear_fila_inicial(tabla.id, id_equipo)
            tablas.append(tabla)
        self.repository.confirmar()
        return tablas

    def calcular_clasificacion_actual(self, id_tabla: int) -> list[FilaPosicionModel]:
        """Filas del grupo ordenadas: 1) puntos, 2) diferencia de goles, 3) goles a favor.
        Si siguen empatados queda primero el equipo inscrito antes (el desempate por enfrentamiento
        directo llega en la Fase 4B)."""
        self.obtener_por_id(id_tabla)
        filas = self.fila_repository.obtener_por_tabla(id_tabla)
        return sorted(
            filas, key=lambda f: (-f.puntos, -f.diferencia_goles, -f.goles_a_favor, f.equipo_id)
        )

    def obtener_por_id(self, id_tabla: int) -> TablaPosicionesModel:
        tabla = self.repository.obtener_por_id(id_tabla)
        if tabla is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "La tabla solicitada no existe.")
        return tabla

    def obtener_por_fase(self, id_fase: int) -> list[TablaPosicionesModel]:
        if self.fase_repository.obtener_por_id(id_fase) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "La fase solicitada no existe.")
        return self.repository.obtener_por_fase(id_fase)
