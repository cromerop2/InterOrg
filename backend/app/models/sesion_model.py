"""Sesiones revocables: se guarda el hash del token, nunca el token entregado."""
from sqlalchemy import Column, String, Integer, ForeignKey
from app.database import Base

class SesionModel(Base):
    __tablename__ = "sesiones"
    token_hash = Column(String(64), primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
    expira_en = Column(Integer, nullable=False)
