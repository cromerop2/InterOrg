"""Acceso a la BD para alineaciones."""

from sqlalchemy.orm import Session

from app.models.alineacion_model import AlineacionModel


class AlineacionRepository:
    def __init__(self, db: Session):
        self.db = db

    def guardar_lista_jugadores(self, filas: list[dict]) -> list[AlineacionModel]:
        """Inserta de una vez a todos los titulares y suplentes (y hace commit de la sesión)."""
        alineaciones = [AlineacionModel(**fila) for fila in filas]
        self.db.add_all(alineaciones)
        self.db.commit()
        for alineacion in alineaciones:
            self.db.refresh(alineacion)
        return alineaciones

    def obtener_por_partido(self, id_partido: int) -> list[AlineacionModel]:
        return (
            self.db.query(AlineacionModel)
            .filter(AlineacionModel.partido_id == id_partido)
            .order_by(AlineacionModel.equipo_id, AlineacionModel.id)
            .all()
        )

    def obtener_por_partido_y_equipo(self, id_partido: int, id_equipo: int) -> list[AlineacionModel]:
        return (
            self.db.query(AlineacionModel)
            .filter(AlineacionModel.partido_id == id_partido, AlineacionModel.equipo_id == id_equipo)
            .order_by(AlineacionModel.id)
            .all()
        )

    def eliminar_planilla(self, id_partido: int, id_equipo: int, confirmar: bool = True) -> None:
        """Borra la planilla de un equipo para rehacerla. Con confirmar=False el borrado se guarda
        junto con la planilla nueva (un solo commit)."""
        self.db.query(AlineacionModel).filter(
            AlineacionModel.partido_id == id_partido, AlineacionModel.equipo_id == id_equipo
        ).delete(synchronize_session=False)
        if confirmar:
            self.db.commit()
