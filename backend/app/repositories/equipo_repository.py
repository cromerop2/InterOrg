"""Acceso a la BD para equipos."""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.enums import EstadoInscripcionEnum
from app.models.equipo_model import EquipoModel
from app.schemas.equipo_schema import EquipoCreate


class EquipoRepository:
    def __init__(self, db: Session):
        self.db = db

    def crear_equipo(self, datos_equipo: EquipoCreate, id_entrenador: int) -> EquipoModel:
        # El estado inicial lo fija el modelo ("Preinscrito").
        equipo = EquipoModel(**datos_equipo.model_dump(), entrenador_id=id_entrenador)
        self.db.add(equipo)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise
        self.db.refresh(equipo)
        return equipo

    def obtener_por_id(self, id_equipo: int) -> EquipoModel | None:
        return self.db.get(EquipoModel, id_equipo)

    def obtener_por_nombre(self, id_torneo: int, nombre: str) -> EquipoModel | None:
        return (
            self.db.query(EquipoModel)
            .filter(EquipoModel.torneo_id == id_torneo, EquipoModel.nombre == nombre)
            .first()
        )

    def obtener_por_torneo(
        self, id_torneo: int, estado: EstadoInscripcionEnum | None = None
    ) -> list[EquipoModel]:
        consulta = self.db.query(EquipoModel).filter(EquipoModel.torneo_id == id_torneo)
        if estado is not None:
            consulta = consulta.filter(EquipoModel.estado_inscripcion == estado)
        return consulta.order_by(EquipoModel.id).all()

    def obtener_por_colegio(self, id_colegio: int) -> list[EquipoModel]:
        return (
            self.db.query(EquipoModel)
            .filter(EquipoModel.colegio_id == id_colegio)
            .order_by(EquipoModel.id)
            .all()
        )

    def actualizar_estado(
        self, id_equipo: int, nuevo_estado: EstadoInscripcionEnum, confirmar: bool = True
    ) -> EquipoModel | None:
        """Cambia el estado de inscripción. Con confirmar=True hace commit de TODA la sesión,
        incluidos los cambios pendientes de otros repositorios (así se guardan juntos)."""
        equipo = self.obtener_por_id(id_equipo)
        if equipo is None:
            return None
        equipo.estado_inscripcion = nuevo_estado
        if confirmar:
            self.db.commit()
            self.db.refresh(equipo)
        return equipo

    def bloquear_plantilla(self, id_equipo: int) -> EquipoModel | None:
        equipo = self.obtener_por_id(id_equipo)
        if equipo is None:
            return None
        equipo.plantilla_bloqueada = True
        self.db.commit()
        self.db.refresh(equipo)
        return equipo

    def bloquear_plantillas_de_torneo(self, id_torneo: int, confirmar: bool = True) -> None:
        """Bloquea las plantillas de todos los equipos del torneo (se usa al iniciarlo)."""
        self.db.query(EquipoModel).filter(EquipoModel.torneo_id == id_torneo).update(
            {EquipoModel.plantilla_bloqueada: True}, synchronize_session="fetch"
        )
        if confirmar:
            self.db.commit()
