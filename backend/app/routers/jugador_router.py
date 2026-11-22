"""Endpoints de jugadores. Sus datos personales solo los ven el Administrador y el entrenador del equipo."""

from fastapi import APIRouter, Depends, Path, status

from app.core.dependencies import get_jugador_service, obtener_usuario_actual, requerir_roles
from app.core.enums import RolEnum
from app.models.usuario_model import UsuarioModel
from app.schemas.jugador_schema import (
    JugadorCreate,
    JugadorResponse,
    JugadorSancionUpdate,
    JugadorTransferencia,
)
from app.services.jugador_service import JugadorService

router = APIRouter(tags=["Jugadores"])

solo_admin = Depends(requerir_roles(RolEnum.ADMINISTRADOR))
solo_entrenador = Depends(requerir_roles(RolEnum.ENTRENADOR))


@router.post(
    "/equipos/{id_equipo}/jugadores", response_model=JugadorResponse, status_code=status.HTTP_201_CREATED
)
def agregar_jugador(
    datos: JugadorCreate,
    id_equipo: int = Path(gt=0),
    entrenador: UsuarioModel = solo_entrenador,
    service: JugadorService = Depends(get_jugador_service),
):
    return service.agregar_jugador_plantilla(id_equipo, datos, entrenador)


@router.get("/equipos/{id_equipo}/jugadores", response_model=list[JugadorResponse])
def obtener_plantilla(
    id_equipo: int = Path(gt=0),
    solo_activos: bool = True,
    usuario: UsuarioModel = Depends(obtener_usuario_actual),
    service: JugadorService = Depends(get_jugador_service),
):
    return service.obtener_por_equipo(id_equipo, usuario, solo_activos)


@router.get("/jugadores/{id_jugador}", response_model=JugadorResponse)
def obtener_jugador(
    id_jugador: int = Path(gt=0),
    usuario: UsuarioModel = Depends(obtener_usuario_actual),
    service: JugadorService = Depends(get_jugador_service),
):
    return service.obtener_por_id(id_jugador, usuario)


@router.post("/jugadores/{id_jugador}/baja", response_model=JugadorResponse)
def dar_de_baja(
    id_jugador: int = Path(gt=0),
    entrenador: UsuarioModel = solo_entrenador,
    service: JugadorService = Depends(get_jugador_service),
):
    """Desactiva al jugador mientras la plantilla no esté bloqueada."""
    return service.dar_de_baja_jugador(id_jugador, entrenador)


@router.patch("/jugadores/{id_jugador}/sancion", response_model=JugadorResponse, dependencies=[solo_admin])
def actualizar_sancion(
    datos: JugadorSancionUpdate,
    id_jugador: int = Path(gt=0),
    service: JugadorService = Depends(get_jugador_service),
):
    return service.actualizar_estado_sancion(id_jugador, datos.sancionado)


@router.post("/jugadores/{id_jugador}/transferir", response_model=JugadorResponse, dependencies=[solo_admin])
def transferir_equipo(
    datos: JugadorTransferencia,
    id_jugador: int = Path(gt=0),
    service: JugadorService = Depends(get_jugador_service),
):
    """Solo si las reglas del torneo tienen permite_transferencias en true."""
    return service.transferir_equipo(id_jugador, datos.nuevo_equipo_id)
