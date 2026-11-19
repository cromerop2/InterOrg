"""Endpoints de fases: la consulta es pública; solo el Administrador las define."""

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.orm import Session

from app.core.dependencies import requerir_roles
from app.core.enums import RolEnum
from app.database import get_db
from app.repositories.fase_repository import FaseRepository
from app.repositories.torneo_repository import TorneoRepository
from app.schemas.fase_schema import ConfiguracionFases, FaseCreate, FaseResponse
from app.services.fase_service import FaseService

router = APIRouter(tags=["Fases"])

solo_admin = Depends(requerir_roles(RolEnum.ADMINISTRADOR))


def get_fase_service(db: Session = Depends(get_db)) -> FaseService:
    return FaseService(FaseRepository(db), TorneoRepository(db))


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
