from sqlalchemy.orm import Session
from app.models.jugador_model import JugadorModel
from app.schemas.jugador_schema import JugadorCreate

class JugadorRepository:
    def __init__(self, db: Session):
        self.db = db

    def crear(self, jugador_data: JugadorCreate) -> JugadorModel:
        # 1. Mapear el schema de Pydantic al modelo de SQLAlchemy
        nuevo_jugador = JugadorModel(**jugador_data.model_dump())
        
        # 2. Agregar y confirmar la transacción en la BD
        self.db.add(nuevo_jugador)
        self.db.commit()
        
        # 3. Refrescar el objeto para obtener el ID generado por la BD
        self.db.refresh(nuevo_jugador)
        
        return nuevo_jugador

    def buscar_por_id(self, jugador_id: int) -> JugadorModel:
        return self.db.query(JugadorModel).filter(JugadorModel.id == jugador_id).first()

    def obtener_todos(self) -> list[JugadorModel]:
        return self.db.query(JugadorModel).all()