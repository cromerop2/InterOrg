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

    def actualizar_goles(
        self,
        marcador: MarcadorModel,
        goles_local: int,
        goles_visitante: int,
        penales_local: int | None = None,
        penales_visitante: int | None = None,
        confirmar: bool = True,
    ) -> MarcadorModel:
        marcador.goles_local = goles_local
        marcador.goles_visitante = goles_visitante
        marcador.goles_penales_local = penales_local
        marcador.goles_penales_visitante = penales_visitante
        return self._guardar(marcador, confirmar)

    def fijar_resultado_final(self, marcador: MarcadorModel, confirmar: bool = True) -> MarcadorModel:
        marcador.es_resultado_final = True
        return self._guardar(marcador, confirmar)

    def _guardar(self, marcador: MarcadorModel, confirmar: bool) -> MarcadorModel:
        if confirmar:
            self.db.commit()
            self.db.refresh(marcador)
        return marcador
