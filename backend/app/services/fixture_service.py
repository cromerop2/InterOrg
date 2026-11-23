"""Programación automática: arma los cruces de una fase y les asigna cancha, fecha y hora sin cruces de horario."""

from collections import defaultdict
from datetime import datetime, time, timedelta

from fastapi import HTTPException, status

from app.core.enums import (
    EstadoFaseEnum,
    EstadoInscripcionEnum,
    EstadoTorneoEnum,
    TipoFormatoEnum,
)
from app.core.reglas import DURACION_PARTIDO_MIN, obtener_regla_entera
from app.models.cancha_model import CanchaModel
from app.models.fase_model import FaseModel
from app.models.partido_model import PartidoModel
from app.models.torneo_model import TorneoModel
from app.repositories.cancha_repository import CanchaRepository
from app.repositories.equipo_repository import EquipoRepository
from app.repositories.fase_repository import FaseRepository
from app.repositories.fila_posicion_repository import FilaPosicionRepository
from app.repositories.marcador_repository import MarcadorRepository
from app.repositories.partido_repository import PartidoRepository
from app.repositories.tabla_posiciones_repository import TablaPosicionesRepository
from app.repositories.torneo_repository import TorneoRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.fixture_schema import FixtureConfiguracion
from app.schemas.partido_schema import PartidoCreate
from app.services.fase_service import FaseService

HORAS_POR_DEFECTO = [time(8), time(10), time(12), time(14), time(16)]


def rondas_todos_contra_todos(ids: list[int]) -> list[list[tuple[int, int]]]:
    """Método del círculo: cada ronda enfrenta a todos los equipos una sola vez (uno descansa si son impares)."""
    lista: list[int | None] = list(ids)
    if len(lista) % 2:
        lista.append(None)  # el equipo emparejado con None descansa
    n = len(lista)
    rondas = []
    for ronda in range(n - 1):
        cruces = []
        for i in range(n // 2):
            a, b = lista[i], lista[n - 1 - i]
            if a is None or b is None:
                continue
            cruces.append((b, a) if (ronda + i) % 2 else (a, b))  # alterna quién es local
        rondas.append(cruces)
        lista = [lista[0], lista[-1]] + lista[1:-1]
    return rondas


class FixtureService:
    def __init__(
        self,
        partido_repository: PartidoRepository,
        marcador_repository: MarcadorRepository,
        fase_repository: FaseRepository,
        torneo_repository: TorneoRepository,
        equipo_repository: EquipoRepository,
        tabla_repository: TablaPosicionesRepository,
        fila_repository: FilaPosicionRepository,
        cancha_repository: CanchaRepository,
        usuario_repository: UsuarioRepository,
        fase_service: FaseService,
    ):
        self.partido_repository = partido_repository
        self.marcador_repository = marcador_repository
        self.fase_repository = fase_repository
        self.torneo_repository = torneo_repository
        self.equipo_repository = equipo_repository
        self.tabla_repository = tabla_repository
        self.fila_repository = fila_repository
        self.cancha_repository = cancha_repository
        self.usuario_repository = usuario_repository
        self.fase_service = fase_service

    def generar_programacion_general(self, id_torneo: int, config: FixtureConfiguracion) -> list[PartidoModel]:
        """Programa la siguiente fase pendiente del torneo (la primera que no ha finalizado)."""
        torneo = self.torneo_repository.obtener_por_id(id_torneo)
        if torneo is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "El torneo solicitado no existe.")
        if torneo.estado != EstadoTorneoEnum.EN_CURSO:
            raise HTTPException(status.HTTP_409_CONFLICT, "El torneo no está En_Curso.")
        pendiente = next(
            (f for f in self.fase_repository.obtener_por_torneo(id_torneo) if f.estado != EstadoFaseEnum.FINALIZADA),
            None,
        )
        if pendiente is None:
            raise HTTPException(status.HTTP_409_CONFLICT, "Todas las fases del torneo ya finalizaron.")
        if self.partido_repository.listar_por_fase(pendiente.id):
            raise HTTPException(
                status.HTTP_409_CONFLICT, f"La fase '{pendiente.nombre}' ya tiene partidos programados."
            )
        return self.generar_fixture(pendiente.id, config)

    def generar_fixture(self, id_fase: int, config: FixtureConfiguracion) -> list[PartidoModel]:
        """Crea los partidos que faltan en la fase: todos contra todos dentro de cada grupo, o los cruces de la
        eliminatoria. Si no alcanzan los horarios del torneo, no se crea ninguno."""
        fase = self.fase_repository.obtener_por_id(id_fase)
        if fase is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "La fase solicitada no existe.")
        torneo = self.torneo_repository.obtener_por_id(fase.torneo_id)
        if torneo.estado != EstadoTorneoEnum.EN_CURSO:
            raise HTTPException(status.HTTP_409_CONFLICT, "El torneo no está En_Curso.")
        if fase.estado != EstadoFaseEnum.PROGRAMADA:
            raise HTTPException(status.HTTP_409_CONFLICT, "La fase ya comenzó o finalizó.")
        fases = self.fase_repository.obtener_por_torneo(torneo.id)
        for anterior in fases:
            if anterior.id < fase.id and anterior.estado != EstadoFaseEnum.FINALIZADA:
                raise HTTPException(status.HTTP_409_CONFLICT, f"La fase anterior '{anterior.nombre}' aún no finaliza.")

        if fase.tipo_formato == TipoFormatoEnum.GRUPOS:
            cruces = self._cruces_de_grupos(fase)
        else:
            cruces = self._cruces_de_eliminatoria(fase, torneo, fases)
        cruces = [c for c in cruces if not self.partido_repository.existe_pareja_en_fase(fase.id, c[0], c[1])]
        if not cruces:
            raise HTTPException(status.HTTP_409_CONFLICT, "No hay cruces por programar en esta fase.")

        canchas = self._canchas(config)
        duracion = obtener_regla_entera(torneo, "duracion_partido_min", DURACION_PARTIDO_MIN)
        piso = None  # una fase nueva empieza el día siguiente al último partido de las anteriores
        if config.fecha_inicio is None:
            anteriores = [p for f in fases if f.id < fase.id for p in self.partido_repository.listar_por_fase(f.id)]
            if anteriores:
                piso = max(p.fecha_hora for p in anteriores).date() + timedelta(days=1)
        horarios = self._horarios(torneo, config, canchas, piso)
        ocupacion = self._ocupacion_actual(horarios, duracion)
        arbitros = self.usuario_repository.obtener_arbitros_activos() if config.asignar_arbitros else []

        creados: list[PartidoModel] = []
        ventana = timedelta(minutes=duracion)

        def libre(ocupados: list[datetime], inicio: datetime) -> bool:
            return all(abs(inicio - otro) >= ventana for otro in ocupados)

        for local, visitante in cruces:
            elegido = next(
                (
                    (inicio, cancha)
                    for inicio, cancha in horarios
                    if libre(ocupacion["cancha", cancha.id], inicio)
                    and libre(ocupacion["equipo", local], inicio)
                    and libre(ocupacion["equipo", visitante], inicio)
                ),
                None,
            )
            if elegido is None:
                self.partido_repository.deshacer()
                raise HTTPException(
                    status.HTTP_409_CONFLICT,
                    "No hay horarios libres suficientes en las fechas del torneo: amplía las horas, canchas o fechas.",
                )
            inicio, cancha = elegido
            arbitro = next((a for a in arbitros if libre(ocupacion["arbitro", a.id], inicio)), None)

            datos = PartidoCreate(
                fase_id=fase.id,
                equipo_local_id=local,
                equipo_visitante_id=visitante,
                cancha_id=cancha.id,
                fecha_hora=inicio,
                arbitro_id=arbitro.id if arbitro else None,
            )
            partido = self.partido_repository.crear_partido(datos, confirmar=False)
            self.marcador_repository.crear_marcador_inicial(partido.id, confirmar=False)
            creados.append(partido)
            ocupacion["cancha", cancha.id].append(inicio)
            ocupacion["equipo", local].append(inicio)
            ocupacion["equipo", visitante].append(inicio)
            if arbitro:
                ocupacion["arbitro", arbitro.id].append(inicio)

        self.partido_repository.confirmar()  # o se crean todos los partidos o ninguno
        return creados

    # ---------- cruces ----------
    def _cruces_de_grupos(self, fase: FaseModel) -> list[tuple[int, int]]:
        tablas = self.tabla_repository.obtener_por_fase(fase.id)
        if not tablas:
            raise HTTPException(status.HTTP_409_CONFLICT, "Arma primero los grupos de la fase.")
        rondas_por_grupo = [
            rondas_todos_contra_todos([f.equipo_id for f in self.fila_repository.obtener_por_tabla(t.id)])
            for t in tablas
        ]
        cruces: list[tuple[int, int]] = []
        for numero in range(max(len(r) for r in rondas_por_grupo)):
            for rondas in rondas_por_grupo:  # la ronda 1 de todos los grupos, luego la ronda 2...
                if numero < len(rondas):
                    cruces.extend(rondas[numero])
        return cruces

    def _cruces_de_eliminatoria(self, fase: FaseModel, torneo: TorneoModel, fases: list[FaseModel]) -> list[tuple[int, int]]:
        """Primero contra último, segundo contra penúltimo... Con una fase anterior, parten de sus clasificados."""
        anteriores = [f for f in fases if f.id < fase.id]
        if anteriores:
            equipos = self.fase_service.determinar_clasificados(anteriores[-1].id)
        else:
            habilitados = self.equipo_repository.obtener_por_torneo(torneo.id, EstadoInscripcionEnum.HABILITADO)
            equipos = [e.id for e in habilitados]
        if len(equipos) < 2 or len(equipos) % 2:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                f"Una eliminatoria necesita un número par de equipos (hay {len(equipos)}).",
            )
        return [(equipos[i], equipos[-1 - i]) for i in range(len(equipos) // 2)]

    # ---------- horarios ----------
    def _canchas(self, config: FixtureConfiguracion) -> list[CanchaModel]:
        activas = self.cancha_repository.obtener_todas(solo_activas=True)
        if config.canchas is not None:
            por_id = {c.id: c for c in activas}
            faltantes = [i for i in config.canchas if i not in por_id]
            if faltantes:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST, f"Canchas inexistentes o inhabilitadas: {faltantes}."
                )
            activas = [por_id[i] for i in dict.fromkeys(config.canchas)]
        if not activas:
            raise HTTPException(status.HTTP_409_CONFLICT, "No hay canchas activas para programar.")
        return activas

    @staticmethod
    def _horarios(torneo: TorneoModel, config: FixtureConfiguracion, canchas: list[CanchaModel], piso=None):
        """Pares (fecha y hora, cancha) en orden cronológico, desde la fecha de inicio hasta el fin del torneo."""
        primer_dia = config.fecha_inicio or max(torneo.fecha_inicio, piso or torneo.fecha_inicio)
        if config.fecha_inicio is None and primer_dia > torneo.fecha_fin:
            raise HTTPException(
                status.HTTP_409_CONFLICT, "Ya no quedan días del torneo después de los partidos de las fases anteriores."
            )
        if not torneo.fecha_inicio <= primer_dia <= torneo.fecha_fin:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "fecha_inicio debe estar dentro de las fechas del torneo.")
        horas = sorted(set(config.horas or HORAS_POR_DEFECTO))
        horarios = []
        dia = primer_dia
        while dia <= torneo.fecha_fin:
            for hora in horas:
                for cancha in canchas:
                    horarios.append((datetime.combine(dia, hora), cancha))
            dia += timedelta(days=1)
        return horarios

    def _ocupacion_actual(self, horarios, duracion: int) -> dict:
        """Horarios ya ocupados por partidos existentes (de cualquier torneo): las canchas se comparten."""
        ocupacion: dict = defaultdict(list)
        margen = timedelta(minutes=duracion)
        desde, hasta = horarios[0][0] - margen, horarios[-1][0] + margen
        for partido in self.partido_repository.listar_en_ventana(desde, hasta):
            ocupacion["cancha", partido.cancha_id].append(partido.fecha_hora)
            ocupacion["equipo", partido.equipo_local_id].append(partido.fecha_hora)
            ocupacion["equipo", partido.equipo_visitante_id].append(partido.fecha_hora)
            if partido.arbitro_id:
                ocupacion["arbitro", partido.arbitro_id].append(partido.fecha_hora)
        return ocupacion
