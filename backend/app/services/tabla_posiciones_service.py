"""Reglas de negocio de grupos y tablas de posiciones."""

from fastapi import HTTPException, status

from app.core.enums import (
    EstadoFaseEnum,
    EstadoInscripcionEnum,
    EstadoPartidoEnum,
    EstadoTorneoEnum,
    TipoFormatoEnum,
)
from app.core.reglas import CLASIFICAN_POR_GRUPO, PUNTOS_EMPATE, PUNTOS_VICTORIA, obtener_regla_entera
from app.models.fila_posicion_model import FilaPosicionModel
from app.models.tabla_posiciones_model import TablaPosicionesModel
from app.repositories.equipo_repository import EquipoRepository
from app.repositories.fase_repository import FaseRepository
from app.repositories.fila_posicion_repository import FilaPosicionRepository
from app.repositories.marcador_repository import MarcadorRepository
from app.repositories.partido_repository import PartidoRepository
from app.repositories.tabla_posiciones_repository import TablaPosicionesRepository
from app.repositories.torneo_repository import TorneoRepository
from app.schemas.tabla_posiciones_schema import GruposConfiguracion

_PARTIDO_TERMINADO = (EstadoPartidoEnum.FINALIZADO, EstadoPartidoEnum.W_O)


class TablaPosicionesService:
    def __init__(
        self,
        repository: TablaPosicionesRepository,
        fila_repository: FilaPosicionRepository,
        fase_repository: FaseRepository,
        torneo_repository: TorneoRepository,
        equipo_repository: EquipoRepository,
        partido_repository: PartidoRepository,
        marcador_repository: MarcadorRepository,
    ):
        self.repository = repository
        self.fila_repository = fila_repository
        self.fase_repository = fase_repository
        self.torneo_repository = torneo_repository
        self.equipo_repository = equipo_repository
        self.partido_repository = partido_repository
        self.marcador_repository = marcador_repository

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
        """Filas del grupo ordenadas: 1) puntos, 2) diferencia de goles, 3) goles a favor y
        4) enfrentamiento directo entre los equipos que sigan empatados. Si aún empatan, el equipo inscrito antes."""
        tabla = self.obtener_por_id(id_tabla)
        filas = sorted(
            self.fila_repository.obtener_por_tabla(id_tabla),
            key=lambda f: (-f.puntos, -f.diferencia_goles, -f.goles_a_favor),
        )
        ordenadas: list[FilaPosicionModel] = []
        i = 0
        while i < len(filas):
            j = i
            while j + 1 < len(filas) and self._clave(filas[j + 1]) == self._clave(filas[i]):
                j += 1
            empatados = filas[i : j + 1]
            ordenadas.extend(self._desempatar(tabla, empatados) if len(empatados) > 1 else empatados)
            i = j + 1
        return ordenadas

    @staticmethod
    def _clave(fila: FilaPosicionModel) -> tuple:
        return (fila.puntos, fila.diferencia_goles, fila.goles_a_favor)

    def _desempatar(self, tabla: TablaPosicionesModel, empatados: list[FilaPosicionModel]) -> list[FilaPosicionModel]:
        """Mini-tabla con solo los partidos terminados entre los equipos empatados: puntos y luego diferencia."""
        fase = self.fase_repository.obtener_por_id(tabla.fase_id)
        torneo = self.torneo_repository.obtener_por_id(fase.torneo_id)
        victoria = obtener_regla_entera(torneo, "puntos_victoria", PUNTOS_VICTORIA)
        empate = obtener_regla_entera(torneo, "puntos_empate", PUNTOS_EMPATE)

        ids = {fila.equipo_id for fila in empatados}
        directo = {id_equipo: [0, 0] for id_equipo in ids}  # [puntos, diferencia de goles]
        for partido in self.partido_repository.listar_por_fase(fase.id):
            if (
                partido.estado not in _PARTIDO_TERMINADO
                or partido.equipo_local_id not in ids
                or partido.equipo_visitante_id not in ids
            ):
                continue
            marcador = self.marcador_repository.obtener_por_partido(partido.id)
            local, visitante = directo[partido.equipo_local_id], directo[partido.equipo_visitante_id]
            local[1] += marcador.goles_local - marcador.goles_visitante
            visitante[1] += marcador.goles_visitante - marcador.goles_local
            if marcador.goles_local > marcador.goles_visitante:
                local[0] += victoria
            elif marcador.goles_local < marcador.goles_visitante:
                visitante[0] += victoria
            else:
                local[0] += empate
                visitante[0] += empate
        return sorted(empatados, key=lambda f: (-directo[f.equipo_id][0], -directo[f.equipo_id][1], f.equipo_id))

    def auditar_y_cerrar_grupo(self, id_tabla: int) -> tuple[TablaPosicionesModel, list[int]]:
        """Cierra el grupo si todos sus partidos terminaron y cada pareja se enfrentó.
        Devuelve la tabla cerrada y los equipos que clasifican, en orden de posición."""
        tabla = self.obtener_por_id(id_tabla)
        fase = self.fase_repository.obtener_por_id(tabla.fase_id)
        torneo = self.torneo_repository.obtener_por_id(fase.torneo_id)
        if torneo.estado != EstadoTorneoEnum.EN_CURSO:
            raise HTTPException(status.HTTP_409_CONFLICT, "El torneo no está En_Curso.")
        if tabla.estado_cierre:
            raise HTTPException(status.HTTP_409_CONFLICT, "El grupo ya está cerrado.")

        equipos = {fila.equipo_id for fila in self.fila_repository.obtener_por_tabla(id_tabla)}
        partidos = [
            p
            for p in self.partido_repository.listar_por_fase(fase.id)
            if p.equipo_local_id in equipos and p.equipo_visitante_id in equipos
        ]
        if any(p.estado not in _PARTIDO_TERMINADO for p in partidos):
            raise HTTPException(status.HTTP_409_CONFLICT, "Aún hay partidos del grupo sin finalizar.")
        enfrentados = {frozenset((p.equipo_local_id, p.equipo_visitante_id)) for p in partidos}
        esperados = len(equipos) * (len(equipos) - 1) // 2
        if len(enfrentados) < esperados:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                f"Faltan {esperados - len(enfrentados)} partidos por jugar para cerrar el grupo.",
            )

        cantidad = obtener_regla_entera(torneo, "clasifican_por_grupo", CLASIFICAN_POR_GRUPO)
        tabla = self.repository.actualizar_estado_cierre(id_tabla, True)
        clasificados = [f.equipo_id for f in self.calcular_clasificacion_actual(id_tabla)[:cantidad]]
        return tabla, clasificados

    def obtener_por_id(self, id_tabla: int) -> TablaPosicionesModel:
        tabla = self.repository.obtener_por_id(id_tabla)
        if tabla is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "La tabla solicitada no existe.")
        return tabla

    def obtener_por_fase(self, id_fase: int) -> list[TablaPosicionesModel]:
        if self.fase_repository.obtener_por_id(id_fase) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "La fase solicitada no existe.")
        return self.repository.obtener_por_fase(id_fase)
