"""Programación automática y corrección de actas: acciones del Administrador."""

from fastapi import APIRouter, Depends, Path, status

from app.core.dependencies import get_acta_service, get_fixture_service, requerir_roles
from app.core.enums import RolEnum
from app.models.usuario_model import UsuarioModel
from app.schemas.acta_schema import ActaCorreccion, AuditoriaActaResponse
from app.schemas.fixture_schema import FixtureConfiguracion
from app.schemas.partido_schema import PartidoResponse
from app.services.acta_service import ActaService
from app.services.fixture_service import FixtureService

router = APIRouter(tags=["Programación y actas"])

solo_admin = Depends(requerir_roles(RolEnum.ADMINISTRADOR))


@router.post(
    "/fases/{id_fase}/fixture",
    response_model=list[PartidoResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[solo_admin],
)
def generar_fixture(
    config: FixtureConfiguracion | None = None,
    id_fase: int = Path(gt=0),
    service: FixtureService = Depends(get_fixture_service),
):
    """Crea los cruces de la fase con cancha, fecha y hora, sin cruces de horario. Todo o nada."""
    return service.generar_fixture(id_fase, config or FixtureConfiguracion())


@router.post(
    "/torneos/{id_torneo}/programacion",
    response_model=list[PartidoResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[solo_admin],
)
def generar_programacion_general(
    config: FixtureConfiguracion | None = None,
    id_torneo: int = Path(gt=0),
    service: FixtureService = Depends(get_fixture_service),
):
    """Programa la siguiente fase pendiente del torneo."""
    return service.generar_programacion_general(id_torneo, config or FixtureConfiguracion())


@router.patch("/partidos/{id_partido}/acta", response_model=PartidoResponse)
def modificar_acta_cerrada(
    datos: ActaCorreccion,
    id_partido: int = Path(gt=0),
    administrador: UsuarioModel = Depends(requerir_roles(RolEnum.ADMINISTRADOR)),
    service: ActaService = Depends(get_acta_service),
):
    """Corrige un acta cerrada (marcador o W.O.), ajusta la tabla y registra el motivo en la auditoría."""
    return service.modificar_acta_cerrada(id_partido, datos, administrador)


@router.get(
    "/partidos/{id_partido}/auditoria", response_model=list[AuditoriaActaResponse], dependencies=[solo_admin]
)
def obtener_auditoria(id_partido: int = Path(gt=0), service: ActaService = Depends(get_acta_service)):
    return service.obtener_auditoria(id_partido)
