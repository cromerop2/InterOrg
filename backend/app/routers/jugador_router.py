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


# REGISTRAR JUGADOR
@router.post("/", response_model=JugadorResponse, status_code=status.HTTP_201_CREATED)
def agregar_jugador(
    jugador: JugadorCreate,  # Pydantic valida automáticamente el Body sin necesidad de Body(...)
    service: JugadorService = Depends(get_jugador_service)
):
    return service.registrar_jugador(jugador)


# OBTENER JUGADOR POR ID
@router.get("/{jugador_id}", response_model=JugadorResponse)
def obtener_jugador(
    jugador_id: int,
    service: JugadorService = Depends(get_jugador_service)
):
    return service.obtener_jugador_por_id(jugador_id)


# OBTENER TODOS LOS JUGADORES
@router.get("/", response_model=list[JugadorResponse])
def obtener_todos_los_jugadores(
    service: JugadorService = Depends(get_jugador_service)
):
    return service.obtener_todos_los_jugadores()