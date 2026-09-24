from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.jugador_schema import JugadorCreate, JugadorResponse
from app.repositories.jugador_repository import JugadorRepository
from app.services.jugador_service import JugadorService

router = APIRouter(prefix="/jugadores", tags=["Jugadores"])

# Inyección de dependencias para el servicio
def get_jugador_service(db: Session = Depends(get_db)) -> JugadorService:
    repository = JugadorRepository(db)
    return JugadorService(repository)

@router.post("/", response_model=JugadorResponse, status_code=status.HTTP_201_CREATED)
def agregar_jugador(
    jugador: JugadorCreate,  # Pydantic valida automáticamente el Body sin necesidad de Body(...)
    service: JugadorService = Depends(get_jugador_service)
):
    return service.registrar_jugador(jugador)