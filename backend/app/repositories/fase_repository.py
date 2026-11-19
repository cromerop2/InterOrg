"""Acceso a la BD para fases."""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.enums import EstadoFaseEnum
from app.models.fase_model import FaseModel
from app.schemas.fase_schema import FaseCreate


class FaseRepository:
    def __init__(self, db: Session):
        self.db = db

    def crear_fase(self, id_torneo: int, datos_fase: FaseCreate) -> FaseModel:
        return self.crear_varias(id_torneo, [datos_fase])[0]

    def crear_varias(self, id_torneo: int, lista_fases: list[FaseCreate]) -> list[FaseModel]:
        """Inserta todas las fases en una sola transacción: o se crean todas o ninguna."""
        fases = [FaseModel(torneo_id=id_torneo, **datos.model_dump()) for datos in lista_fases]
        self.db.add_all(fases)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise
        for fase in fases:
            self.db.refresh(fase)
        return fases

    def obtener_por_id(self, id_fase: int) -> FaseModel | None:
        return self.db.get(FaseModel, id_fase)

    def obtener_por_torneo(self, id_torneo: int) -> list[FaseModel]:
        """Fases del torneo en el orden en que se crearon (orden de juego)."""
        return (
            self.db.query(FaseModel)
            .filter(FaseModel.torneo_id == id_torneo)
            .order_by(FaseModel.id)
            .all()
        )

    def obtener_por_nombre(self, id_torneo: int, nombre: str) -> FaseModel | None:
        return (
            self.db.query(FaseModel)
            .filter(FaseModel.torneo_id == id_torneo, FaseModel.nombre == nombre)
            .first()
        )

    def actualizar_estado(self, id_fase: int, nuevo_estado: EstadoFaseEnum) -> FaseModel | None:
        fase = self.obtener_por_id(id_fase)
        if fase is None:
            return None
        fase.estado = nuevo_estado
        self.db.commit()
        self.db.refresh(fase)
        return fase
