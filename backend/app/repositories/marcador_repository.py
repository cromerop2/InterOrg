"""Acceso a la BD para marcadores."""

from sqlalchemy.orm import Session

from app.models.marcador_model import MarcadorModel


class MarcadorRepository:
    def __init__(self, db: Session):
        self.db = db

    def crear_marcador_inicial(self, id_partido: int) -> MarcadorModel:
        """Inserta el 0-0 de un partido nuevo. Hace commit de toda la sesión (incluido el partido)."""
        marcador = MarcadorModel(partido_id=id_partido)
        self.db.add(marcador)
        self.db.commit()
        self.db.refresh(marcador)
        return marcador

    def obtener_por_partido(self, id_partido: int) -> MarcadorModel | None:
        return self.db.query(MarcadorModel).filter(MarcadorModel.partido_id == id_partido).first()
