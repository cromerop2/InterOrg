from sqlalchemy import Column, Integer, String, Date
from app.database import Base

class JugadorModel(Base):
    __tablename__ = "jugadores"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(100), nullable=False)
    identificacion = Column(String(20), unique=True, nullable=False)
    fecha_nacimiento = Column(String(10), nullable=True)
    numero_camiseta = Column(Integer, nullable=False)
    posicion = Column(String(50), nullable=False) 