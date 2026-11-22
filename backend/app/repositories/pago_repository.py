"""Acceso a la BD para pagos."""

from sqlalchemy.orm import Session

from app.core.enums import EstadoPagoEnum
from app.models.pago_model import PagoModel
from app.schemas.pago_schema import PagoCreate


class PagoRepository:
    def __init__(self, db: Session):
        self.db = db

    def crear_pago(self, id_equipo: int, datos_pago: PagoCreate) -> PagoModel:
        # El estado inicial lo fija el modelo ("Pendiente").
        pago = PagoModel(equipo_id=id_equipo, **datos_pago.model_dump())
        self.db.add(pago)
        self.db.commit()
        self.db.refresh(pago)
        return pago

    def obtener_por_id(self, id_pago: int) -> PagoModel | None:
        return self.db.get(PagoModel, id_pago)

    def obtener_por_equipo(self, id_equipo: int) -> list[PagoModel]:
        return (
            self.db.query(PagoModel)
            .filter(PagoModel.equipo_id == id_equipo)
            .order_by(PagoModel.id)
            .all()
        )

    def obtener_todos(self, estado: EstadoPagoEnum | None = None) -> list[PagoModel]:
        consulta = self.db.query(PagoModel)
        if estado is not None:
            consulta = consulta.filter(PagoModel.estado == estado)
        return consulta.order_by(PagoModel.id).all()

    def obtener_por_referencia(self, referencia: str) -> PagoModel | None:
        """Pago vigente (no rechazado) que ya usa esa referencia bancaria."""
        return (
            self.db.query(PagoModel)
            .filter(
                PagoModel.referencia_transaccion == referencia,
                PagoModel.estado != EstadoPagoEnum.RECHAZADO,
            )
            .first()
        )

    def existe_aprobado(self, id_equipo: int) -> bool:
        return (
            self.db.query(PagoModel.id)
            .filter(PagoModel.equipo_id == id_equipo, PagoModel.estado == EstadoPagoEnum.APROBADO)
            .first()
            is not None
        )

    def actualizar_estado(
        self,
        id_pago: int,
        nuevo_estado: EstadoPagoEnum,
        observaciones: str | None = None,
        confirmar: bool = True,
    ) -> PagoModel | None:
        """Con confirmar=False el cambio queda pendiente y se guarda junto al del siguiente repositorio."""
        pago = self.obtener_por_id(id_pago)
        if pago is None:
            return None
        pago.estado = nuevo_estado
        if observaciones is not None:
            pago.observaciones = observaciones
        if confirmar:
            self.db.commit()
            self.db.refresh(pago)
        return pago
