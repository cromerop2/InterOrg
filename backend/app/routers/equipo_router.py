"""Endpoints de equipos: el Entrenador inscribe; el Administrador audita y descalifica."""

from fastapi import APIRouter, Depends, Path, status

from app.core.dependencies import (
    get_equipo_service,
    obtener_usuario_actual,
    requerir_roles,
)
from app.core.enums import RolEnum
from app.models.usuario_model import UsuarioModel
from app.schemas.equipo_schema import EquipoAuditoria, EquipoCreate, EquipoResponse
from app.schemas.tabla_posiciones_schema import FilaPosicionResponse
from app.services.equipo_service import EquipoService

router = APIRouter(tags=["Equipos"])

solo_admin = Depends(requerir_roles(RolEnum.ADMINISTRADOR))
con_sesion = Depends(obtener_usuario_actual)


@router.post("/equipos/", response_model=EquipoResponse, status_code=status.HTTP_201_CREATED)
def registrar_equipo(
    datos: EquipoCreate,
    entrenador: UsuarioModel = Depends(requerir_roles(RolEnum.ENTRENADOR)),
    service: EquipoService = Depends(get_equipo_service),
):
    """Inscribe un equipo del entrenador autenticado (estado inicial Preinscrito)."""
    return service.registrar_equipo(datos, entrenador)


@router.get("/equipos/{id_equipo}", response_model=EquipoResponse)
def obtener_por_id(
    id_equipo: int = Path(gt=0),
    usuario: UsuarioModel = Depends(obtener_usuario_actual),
    service: EquipoService = Depends(get_equipo_service),
):
    """Un Administrador ve cualquier equipo; un Entrenador solo los suyos."""
    return service.obtener_por_id(id_equipo, usuario)


@router.get("/torneos/{id_torneo}/equipos", response_model=list[EquipoResponse], dependencies=[con_sesion])
def obtener_por_torneo(id_torneo: int = Path(gt=0), service: EquipoService = Depends(get_equipo_service)):
    return service.obtener_por_torneo(id_torneo)


@router.patch("/equipos/{id_equipo}/auditar", response_model=EquipoResponse, dependencies=[solo_admin])
def auditar_inscripcion(
    datos: EquipoAuditoria,
    id_equipo: int = Path(gt=0),
    service: EquipoService = Depends(get_equipo_service),
):
    """Aprueba el pago indicado y habilita el equipo si tiene el mínimo de jugadores."""
    return service.auditar_inscripcion_equipo(id_equipo, datos.id_pago)


@router.post("/equipos/{id_equipo}/descalificar", response_model=EquipoResponse, dependencies=[solo_admin])
def descalificar(id_equipo: int = Path(gt=0), service: EquipoService = Depends(get_equipo_service)):
    return service.descalificar(id_equipo)


@router.get("/equipos/{id_equipo}/estadisticas", response_model=list[FilaPosicionResponse])
def obtener_estadisticas_actuales(
    id_equipo: int = Path(gt=0),
    usuario: UsuarioModel = Depends(obtener_usuario_actual),
    service: EquipoService = Depends(get_equipo_service),
):
    """Puntos, goles y rendimiento del equipo en cada grupo. Lo ve su entrenador o un Administrador."""
    return service.obtener_estadisticas_actuales(id_equipo, usuario)
