"""Endpoints de fases: la consulta es pública; solo el Administrador las define."""

from fastapi import APIRouter, Depends, Path, status

from app.core.dependencies import get_fase_service, requerir_roles
from app.core.enums import RolEnum
from app.schemas.fase_schema import ClasificadosResponse, ConfiguracionFases, FaseCreate, FaseResponse
from app.services.fase_service import FaseService

router = APIRouter(tags=["Fases"])

solo_admin = Depends(requerir_roles(RolEnum.ADMINISTRADOR))


@router.post(
    "/torneos/{id_torneo}/fases",
    response_model=FaseResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[solo_admin],
)
def crear_fase(datos: FaseCreate, id_torneo: int = Path(gt=0), service: FaseService = Depends(get_fase_service)):
    """Agrega una fase al final del torneo (solo en estado Inscripciones)."""
    return service.crear_fase(id_torneo, datos)


@router.post(
    "/torneos/{id_torneo}/fases/estructurar",
    response_model=list[FaseResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[solo_admin],
)
def estructurar_fases(
    configuracion: ConfiguracionFases,
    id_torneo: int = Path(gt=0),
    service: FaseService = Depends(get_fase_service),
):
    """Crea todas las fases de un torneo que aún no tiene ninguna, en el orden recibido."""
    return service.estructurar_fases(id_torneo, configuracion)


@router.get("/torneos/{id_torneo}/fases", response_model=list[FaseResponse])
def obtener_por_torneo(id_torneo: int = Path(gt=0), service: FaseService = Depends(get_fase_service)):
    return service.obtener_por_torneo(id_torneo)


@router.get("/fases/{id_fase}", response_model=FaseResponse)
def obtener_por_id(id_fase: int = Path(gt=0), service: FaseService = Depends(get_fase_service)):
    return service.obtener_por_id(id_fase)


@router.post("/fases/{id_fase}/cerrar", response_model=FaseResponse, dependencies=[solo_admin])
def cerrar_fase(id_fase: int = Path(gt=0), service: FaseService = Depends(get_fase_service)):
    """Finaliza la fase (todos sus partidos terminados y, en grupos, todos los grupos cerrados)."""
    return service.cerrar_fase(id_fase)


@router.get("/fases/{id_fase}/clasificados", response_model=ClasificadosResponse)
def determinar_clasificados(id_fase: int = Path(gt=0), service: FaseService = Depends(get_fase_service)):
    """Equipos que avanzan de la fase (público)."""
    return ClasificadosResponse(fase_id=id_fase, clasificados=service.determinar_clasificados(id_fase))
