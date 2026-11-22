"""Acceso a la BD para partidos."""

from datetime import date, datetime, time, timedelta

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.core.enums import EstadoPartidoEnum
from app.models.partido_model import PartidoModel
from app.schemas.partido_schema import PartidoCreate


class PartidoRepository:
    def __init__(self, db: Session):
        self.db = db

    def crear_partido(self, datos_partido: PartidoCreate, confirmar: bool = True) -> PartidoModel:
        """Inserta el cruce con estado "Programado". Con confirmar=False solo lo envía a la BD
        (para tener su id) y el commit lo hace el siguiente repositorio que comparte la sesión."""
        partido = PartidoModel(**datos_partido.model_dump())
        self.db.add(partido)
        if confirmar:
            self.db.commit()
            self.db.refresh(partido)
        else:
            self.db.flush()
        return partido

    def obtener_por_id(self, id_partido: int) -> PartidoModel | None:
        return self.db.get(PartidoModel, id_partido)

    def listar_por_fase(self, id_fase: int) -> list[PartidoModel]:
        return (
            self.db.query(PartidoModel)
            .filter(PartidoModel.fase_id == id_fase)
            .order_by(PartidoModel.fecha_hora, PartidoModel.id)
            .all()
        )

    def listar_por_equipo(self, id_equipo: int) -> list[PartidoModel]:
        """Partidos donde el equipo es local o visitante."""
        return (
            self.db.query(PartidoModel)
            .filter(or_(PartidoModel.equipo_local_id == id_equipo, PartidoModel.equipo_visitante_id == id_equipo))
            .order_by(PartidoModel.fecha_hora, PartidoModel.id)
            .all()
        )

    def listar_por_arbitro(self, id_arbitro: int) -> list[PartidoModel]:
        return (
            self.db.query(PartidoModel)
            .filter(PartidoModel.arbitro_id == id_arbitro)
            .order_by(PartidoModel.fecha_hora, PartidoModel.id)
            .all()
        )

    def listar_por_cancha_y_fecha(self, id_cancha: int, fecha: date) -> list[PartidoModel]:
        inicio = datetime.combine(fecha, time.min)
        return (
            self.db.query(PartidoModel)
            .filter(
                PartidoModel.cancha_id == id_cancha,
                PartidoModel.fecha_hora >= inicio,
                PartidoModel.fecha_hora < inicio + timedelta(days=1),
            )
            .order_by(PartidoModel.fecha_hora, PartidoModel.id)
            .all()
        )

    # ---------- cruces de horario ----------
    # Dos partidos se cruzan si empiezan con menos de `duracion_min` minutos de diferencia.
    # Un partido "Suspendido" libera su horario.
    def _cruce(self, inicio: datetime, duracion_min: int, excluir_id: int | None, *condiciones):
        ventana = timedelta(minutes=duracion_min)
        consulta = self.db.query(PartidoModel).filter(
            PartidoModel.estado != EstadoPartidoEnum.SUSPENDIDO,
            PartidoModel.fecha_hora > inicio - ventana,
            PartidoModel.fecha_hora < inicio + ventana,
            *condiciones,
        )
        if excluir_id is not None:
            consulta = consulta.filter(PartidoModel.id != excluir_id)
        return consulta.first()

    def cruce_en_cancha(self, id_cancha, inicio, duracion_min, excluir_id=None) -> PartidoModel | None:
        return self._cruce(inicio, duracion_min, excluir_id, PartidoModel.cancha_id == id_cancha)

    def cruce_de_equipos(self, ids_equipos, inicio, duracion_min, excluir_id=None) -> PartidoModel | None:
        return self._cruce(
            inicio,
            duracion_min,
            excluir_id,
            or_(PartidoModel.equipo_local_id.in_(ids_equipos), PartidoModel.equipo_visitante_id.in_(ids_equipos)),
        )

    def cruce_de_arbitro(self, id_arbitro, inicio, duracion_min, excluir_id=None) -> PartidoModel | None:
        return self._cruce(inicio, duracion_min, excluir_id, PartidoModel.arbitro_id == id_arbitro)

    def existe_pareja_en_fase(self, id_fase: int, id_a: int, id_b: int) -> bool:
        """True si esos dos equipos ya tienen un partido en la fase (en cualquier orden)."""
        return (
            self.db.query(PartidoModel.id)
            .filter(
                PartidoModel.fase_id == id_fase,
                or_(
                    and_(PartidoModel.equipo_local_id == id_a, PartidoModel.equipo_visitante_id == id_b),
                    and_(PartidoModel.equipo_local_id == id_b, PartidoModel.equipo_visitante_id == id_a),
                ),
            )
            .first()
            is not None
        )

    # ---------- cambios ----------
    def actualizar_estado(
        self, id_partido: int, nuevo_estado: EstadoPartidoEnum, confirmar: bool = True
    ) -> PartidoModel | None:
        partido = self.obtener_por_id(id_partido)
        if partido is None:
            return None
        partido.estado = nuevo_estado
        if confirmar:
            self.db.commit()
            self.db.refresh(partido)
        return partido

    def reprogramar(
        self, partido: PartidoModel, nueva_fecha: datetime, nueva_cancha: int, nuevo_estado: EstadoPartidoEnum
    ) -> PartidoModel:
        partido.fecha_hora = nueva_fecha
        partido.cancha_id = nueva_cancha
        partido.estado = nuevo_estado
        self.db.commit()
        self.db.refresh(partido)
        return partido

    def asignar_arbitro(self, partido: PartidoModel, id_arbitro: int) -> PartidoModel:
        partido.arbitro_id = id_arbitro
        self.db.commit()
        self.db.refresh(partido)
        return partido
