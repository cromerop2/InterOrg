"""Acceso a la BD para tablas de posiciones (grupos)."""

from sqlalchemy.orm import Session

from app.models.fila_posicion_model import FilaPosicionModel
from app.models.tabla_posiciones_model import TablaPosicionesModel


class TablaPosicionesRepository:
    def __init__(self, db: Session):
        self.db = db

    def crear_tabla(self, id_fase: int, nombre_grupo: str, confirmar: bool = True) -> TablaPosicionesModel:
        tabla = TablaPosicionesModel(fase_id=id_fase, nombre_grupo=nombre_grupo)
        self.db.add(tabla)
        if confirmar:
            self.db.commit()
            self.db.refresh(tabla)
        else:
            self.db.flush()  # asigna el id sin cerrar la transacción
        return tabla

    def confirmar(self) -> None:
        self.db.commit()

    def obtener_por_fase(self, id_fase: int) -> list[TablaPosicionesModel]:
        return (
            self.db.query(TablaPosicionesModel)
            .filter(TablaPosicionesModel.fase_id == id_fase)
            .order_by(TablaPosicionesModel.id)
            .all()
        )

    def obtener_por_id(self, id_tabla: int) -> TablaPosicionesModel | None:
        return self.db.get(TablaPosicionesModel, id_tabla)

    def obtener_por_fase_y_equipo(self, id_fase: int, id_equipo: int) -> TablaPosicionesModel | None:
        """Grupo de la fase en el que juega el equipo."""
        return (
            self.db.query(TablaPosicionesModel)
            .join(FilaPosicionModel, FilaPosicionModel.tabla_id == TablaPosicionesModel.id)
            .filter(TablaPosicionesModel.fase_id == id_fase, FilaPosicionModel.equipo_id == id_equipo)
            .first()
        )

    def actualizar_estado_cierre(self, id_tabla: int, cerrado: bool) -> TablaPosicionesModel | None:
        tabla = self.obtener_por_id(id_tabla)
        if tabla is None:
            return None
        tabla.estado_cierre = cerrado
        self.db.commit()
        self.db.refresh(tabla)
        return tabla
