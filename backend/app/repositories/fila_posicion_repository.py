"""Acceso a la BD para las filas de las tablas de posiciones."""

from sqlalchemy.orm import Session

from app.models.fila_posicion_model import FilaPosicionModel


class FilaPosicionRepository:
    def __init__(self, db: Session):
        self.db = db

    def crear_fila_inicial(self, id_tabla: int, id_equipo: int) -> FilaPosicionModel:
        """Inserta la fila en ceros. No hace commit: lo hace quien arma el grupo completo."""
        fila = FilaPosicionModel(tabla_id=id_tabla, equipo_id=id_equipo)
        self.db.add(fila)
        return fila

    def obtener_por_tabla(self, id_tabla: int) -> list[FilaPosicionModel]:
        return (
            self.db.query(FilaPosicionModel)
            .filter(FilaPosicionModel.tabla_id == id_tabla)
            .order_by(FilaPosicionModel.id)
            .all()
        )

    def obtener_por_tabla_y_equipo(self, id_tabla: int, id_equipo: int) -> FilaPosicionModel | None:
        return (
            self.db.query(FilaPosicionModel)
            .filter(FilaPosicionModel.tabla_id == id_tabla, FilaPosicionModel.equipo_id == id_equipo)
            .first()
        )
