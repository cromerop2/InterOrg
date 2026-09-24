from fastapi import APIRouter, Body
from app.schemas import JugadorCreate, JugadorResponse

router = APIRouter(
    prefix="/jugadores",
    tags=["Jugadores"]
)

jugadores = []

@router.get("/", response_model=list[JugadorResponse])
def obtener_jugadores():
    return jugadores

@router.post("/", response_model=JugadorResponse)
def agregar_jugador(jugador: JugadorCreate = Body(...)):
    nuevo_jugador = jugador.model_dump()
    nuevo_jugador["id"] = len(jugadores) + 1
    jugadores.append(nuevo_jugador)
    return JugadorResponse(**nuevo_jugador)