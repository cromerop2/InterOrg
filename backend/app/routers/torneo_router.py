"""Endpoints de torneos: la consulta es pública (espectadores); solo el Administrador modifica."""

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.orm import Session

from app.core.dependencies import requerir_roles
from app.core.enums import EstadoTorneoEnum, RolEnum
from app.database import get_db
from app.repositories.equipo_repository import EquipoRepository
from app.repositories.torneo_repository import TorneoRepository
from app.schemas.torneo_schema import TorneoCreate, TorneoResponse, TorneoUpdate
from app.services.torneo_service import TorneoService

router = APIRouter(prefix="/torneos", tags=["Torneos"])

solo_admin = Depends(requerir_roles(RolEnum.ADMINISTRADOR))


def get_torneo_service(db: Session = Depends(get_db)) -> TorneoService:
    return TorneoService(TorneoRepository(db), EquipoRepository(db))


@router.post("/", response_model=TorneoResponse, status_code=status.HTTP_201_CREATED, dependencies=[solo_admin])
def crear_torneo(datos: TorneoCreate, service: TorneoService = Depends(get_torneo_service)):
    return service.crear_torneo(datos)


@router.get("/", response_model=list[TorneoResponse])
def obtener_todos(estado: EstadoTorneoEnum | None = None, service: TorneoService = Depends(get_torneo_service)):
    """Público. Con ?estado=En_Curso (u otro) filtra por estado."""
    return service.obtener_todos(estado)


@router.get("/{id_torneo}", response_model=TorneoResponse)
def obtener_por_id(id_torneo: int = Path(gt=0), service: TorneoService = Depends(get_torneo_service)):
    return service.obtener_por_id(id_torneo)


@router.patch("/{id_torneo}", response_model=TorneoResponse, dependencies=[solo_admin])
def actualizar_detalles(
    datos: TorneoUpdate,
    id_torneo: int = Path(gt=0),
    service: TorneoService = Depends(get_torneo_service),
):
    return service.actualizar_detalles(id_torneo, datos)


@router.post("/{id_torneo}/iniciar", response_model=TorneoResponse, dependencies=[solo_admin])
def iniciar_torneo(id_torneo: int = Path(gt=0), service: TorneoService = Depends(get_torneo_service)):
    """Exige el mínimo de equipos Habilitados y bloquea las plantillas de todos los equipos."""
    return service.iniciar_torneo(id_torneo)


@router.post("/{id_torneo}/finalizar", response_model=TorneoResponse, dependencies=[solo_admin])
def finalizar_torneo(id_torneo: int = Path(gt=0), service: TorneoService = Depends(get_torneo_service)):
    return service.finalizar_torneo(id_torneo)


@router.post("/{id_torneo}/cancelar", response_model=TorneoResponse, dependencies=[solo_admin])
def cancelar_torneo(id_torneo: int = Path(gt=0), service: TorneoService = Depends(get_torneo_service)):
    return service.cancelar_torneo(id_torneo)
