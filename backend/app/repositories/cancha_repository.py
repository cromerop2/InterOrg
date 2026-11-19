"""Acceso a la BD para canchas."""

from sqlalchemy.orm import Session

from app.models.cancha_model import CanchaModel
from app.schemas.cancha_schema import CanchaCreate, CanchaUpdate


class CanchaRepository:
    def __init__(self, db: Session):
        self.db = db

    def crear_cancha(self, datos_cancha: CanchaCreate) -> CanchaModel:
        cancha = CanchaModel(**datos_cancha.model_dump())
        self.db.add(cancha)
        self.db.commit()
        self.db.refresh(cancha)
        return cancha

    def obtener_por_id(self, id_cancha: int) -> CanchaModel | None:
        return self.db.get(CanchaModel, id_cancha)

    def obtener_todas(self, solo_activas: bool = True) -> list[CanchaModel]:
        consulta = self.db.query(CanchaModel)
        if solo_activas:
            consulta = consulta.filter(CanchaModel.estado_activo.is_(True))
        return consulta.order_by(CanchaModel.id).all()

    def actualizar_detalles(self, id_cancha: int, datos: CanchaUpdate) -> CanchaModel | None:
        cancha = self.obtener_por_id(id_cancha)
        if cancha is None:
            return None
        for campo, valor in datos.model_dump(exclude_unset=True).items():
            setattr(cancha, campo, valor)
        self.db.commit()
        self.db.refresh(cancha)
        return cancha

    def modificar_estado(self, id_cancha: int, activo: bool) -> CanchaModel | None:
        """Inhabilita o rehabilita una cancha sin borrarla. None si no existe."""
        cancha = self.obtener_por_id(id_cancha)
        if cancha is None:
            return None
        cancha.estado_activo = activo
        self.db.commit()
        self.db.refresh(cancha)
        return cancha
