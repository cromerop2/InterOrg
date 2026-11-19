"""Acceso a la BD para torneos."""

from sqlalchemy.orm import Session

from app.core.enums import EstadoTorneoEnum
from app.models.torneo_model import TorneoModel
from app.schemas.torneo_schema import TorneoCreate, TorneoUpdate


class TorneoRepository:
    def __init__(self, db: Session):
        self.db = db

    def crear_torneo(self, datos_torneo: TorneoCreate) -> TorneoModel:
        # El estado inicial lo fija el modelo ("Inscripciones").
        torneo = TorneoModel(**datos_torneo.model_dump())
        self.db.add(torneo)
        self.db.commit()
        self.db.refresh(torneo)
        return torneo

    def obtener_por_id(self, id_torneo: int) -> TorneoModel | None:
        return self.db.get(TorneoModel, id_torneo)

    def obtener_todos(self, estado_filtro: EstadoTorneoEnum | None = None) -> list[TorneoModel]:
        consulta = self.db.query(TorneoModel)
        if estado_filtro is not None:
            consulta = consulta.filter(TorneoModel.estado == estado_filtro)
        return consulta.order_by(TorneoModel.id).all()

    def actualizar_detalles(self, id_torneo: int, datos: TorneoUpdate) -> TorneoModel | None:
        torneo = self.obtener_por_id(id_torneo)
        if torneo is None:
            return None
        for campo, valor in datos.model_dump(exclude_unset=True).items():
            setattr(torneo, campo, valor)
        self.db.commit()
        self.db.refresh(torneo)
        return torneo

    def actualizar_estado(self, id_torneo: int, nuevo_estado: EstadoTorneoEnum) -> TorneoModel | None:
        torneo = self.obtener_por_id(id_torneo)
        if torneo is None:
            return None
        torneo.estado = nuevo_estado
        self.db.commit()
        self.db.refresh(torneo)
        return torneo
