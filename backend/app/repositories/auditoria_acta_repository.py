"""Acceso a la BD para el registro de correcciones de actas."""

from sqlalchemy.orm import Session

from app.models.auditoria_acta_model import AuditoriaActaModel


class AuditoriaActaRepository:
    def __init__(self, db: Session):
        self.db = db

    def registrar(
        self, id_partido: int, id_usuario: int, motivo: str, datos_anteriores: dict, datos_nuevos: dict
    ) -> AuditoriaActaModel:
        """Guarda la auditoría y hace commit de toda la sesión: la corrección y su registro van juntos."""
        registro = AuditoriaActaModel(
            partido_id=id_partido,
            usuario_id=id_usuario,
            motivo=motivo,
            datos_anteriores=datos_anteriores,
            datos_nuevos=datos_nuevos,
        )
        self.db.add(registro)
        self.db.commit()
        self.db.refresh(registro)
        return registro

    def obtener_por_partido(self, id_partido: int) -> list[AuditoriaActaModel]:
        return (
            self.db.query(AuditoriaActaModel)
            .filter(AuditoriaActaModel.partido_id == id_partido)
            .order_by(AuditoriaActaModel.id)
            .all()
        )
