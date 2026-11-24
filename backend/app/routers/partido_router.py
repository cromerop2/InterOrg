"""Endpoints de partidos y alineaciones. El calendario es público; programar es del Administrador."""

from fastapi import APIRouter, Depends, Path, status

from app.core.dependencies import (
    get_alineacion_service,
    get_partido_service,
    obtener_usuario_actual,
    requerir_roles,
)
from app.core.enums import RolEnum
from app.models.usuario_model import UsuarioModel
from app.schemas.alineacion_schema import AlineacionDetalleResponse, AlineacionEnvio, AlineacionResponse
from app.schemas.marcador_schema import MarcadorResponse
from app.schemas.partido_schema import (
    PartidoArbitro,
    PartidoCreate,
    PartidoReprogramacion,
    PartidoResponse,
)
from app.services.alineacion_service import AlineacionService
from app.services.partido_service import PartidoService

router = APIRouter(tags=["Partidos"])

solo_admin = Depends(requerir_roles(RolEnum.ADMINISTRADOR))
con_sesion = Depends(obtener_usuario_actual)


@router.post("/partidos/", response_model=PartidoResponse, status_code=status.HTTP_201_CREATED, dependencies=[solo_admin])
def programar_encuentro(datos: PartidoCreate, service: PartidoService = Depends(get_partido_service)):
    """Programa un cruce: valida fase, equipos Habilitados, fechas del torneo, cancha, árbitro y cruces de horario."""
    return service.programar_encuentro(datos)


# Esta ruta va antes de /partidos/{id_partido} para que "mis-asignaciones" no se tome como un id.
@router.get("/partidos/mis-asignaciones", response_model=list[PartidoResponse])
def consultar_asignaciones(
    arbitro: UsuarioModel = Depends(requerir_roles(RolEnum.ARBITRO)),
    service: PartidoService = Depends(get_partido_service),
):
    """Partidos en los que el administrador designó al árbitro autenticado."""
    return service.consultar_asignaciones(arbitro.id)


@router.get("/partidos/{id_partido}", response_model=PartidoResponse)
def obtener_partido(id_partido: int = Path(gt=0), service: PartidoService = Depends(get_partido_service)):
    return service.obtener_por_id(id_partido)


@router.get("/partidos/{id_partido}/marcador", response_model=MarcadorResponse)
def obtener_marcador(id_partido: int = Path(gt=0), service: PartidoService = Depends(get_partido_service)):
    return service.obtener_marcador(id_partido)


@router.patch("/partidos/{id_partido}/reprogramar", response_model=PartidoResponse, dependencies=[solo_admin])
def reprogramar_encuentro(
    datos: PartidoReprogramacion,
    id_partido: int = Path(gt=0),
    service: PartidoService = Depends(get_partido_service),
):
    return service.reprogramar_encuentro(id_partido, datos.fecha_hora, datos.cancha_id)


@router.post("/partidos/{id_partido}/suspender", response_model=PartidoResponse, dependencies=[solo_admin])
def suspender_partido(id_partido: int = Path(gt=0), service: PartidoService = Depends(get_partido_service)):
    return service.suspender_partido(id_partido)


@router.put("/partidos/{id_partido}/arbitro", response_model=PartidoResponse, dependencies=[solo_admin])
def asignar_arbitro(
    datos: PartidoArbitro,
    id_partido: int = Path(gt=0),
    service: PartidoService = Depends(get_partido_service),
):
    return service.asignar_arbitro_partido(id_partido, datos.arbitro_id)


@router.get("/fases/{id_fase}/partidos", response_model=list[PartidoResponse])
def listar_por_fase(id_fase: int = Path(gt=0), service: PartidoService = Depends(get_partido_service)):
    """Calendario de una fase (público)."""
    return service.listar_por_fase(id_fase)


@router.get("/equipos/{id_equipo}/calendario", response_model=list[PartidoResponse])
def consultar_calendario(
    id_equipo: int = Path(gt=0),
    usuario: UsuarioModel = Depends(obtener_usuario_actual),
    service: PartidoService = Depends(get_partido_service),
):
    """Partidos del equipo como local o visitante. Lo ve su entrenador o un Administrador."""
    return service.consultar_calendario(id_equipo, usuario)


# ---------- alineaciones ----------
@router.put("/partidos/{id_partido}/equipos/{id_equipo}/alineacion", response_model=list[AlineacionResponse])
def enviar_alineacion(
    datos: AlineacionEnvio,
    id_partido: int = Path(gt=0),
    id_equipo: int = Path(gt=0),
    entrenador: UsuarioModel = Depends(requerir_roles(RolEnum.ENTRENADOR)),
    service: AlineacionService = Depends(get_alineacion_service),
):
    """El entrenador dueño envía la planilla completa; si ya había una, la reemplaza (con el partido Programado)."""
    return service.enviar_planilla_oficial(id_partido, id_equipo, datos.jugadores, entrenador)


@router.get("/partidos/{id_partido}/alineaciones", response_model=list[AlineacionDetalleResponse], dependencies=[con_sesion])
def obtener_alineaciones(id_partido: int = Path(gt=0), service: AlineacionService = Depends(get_alineacion_service)):
    return service.obtener_detalle_por_partido(id_partido)
