"""Endpoints de canchas: cualquier usuario con sesión consulta; solo el Administrador modifica."""

from datetime import date

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.orm import Session

from app.core.dependencies import obtener_usuario_actual, requerir_roles
from app.core.enums import RolEnum
from app.database import get_db
from app.repositories.cancha_repository import CanchaRepository
from app.repositories.partido_repository import PartidoRepository
from app.schemas.partido_schema import PartidoResponse
from app.schemas.cancha_schema import (
    CanchaCreate,
    CanchaEstadoUpdate,
    CanchaResponse,
    CanchaUpdate,
)
from app.services.cancha_service import CanchaService

router = APIRouter(prefix="/canchas", tags=["Canchas"])

solo_admin = Depends(requerir_roles(RolEnum.ADMINISTRADOR))
con_sesion = Depends(obtener_usuario_actual)


def get_cancha_service(db: Session = Depends(get_db)) -> CanchaService:
    return CanchaService(CanchaRepository(db), PartidoRepository(db))


@router.post("/", response_model=CanchaResponse, status_code=status.HTTP_201_CREATED, dependencies=[solo_admin])
def crear_cancha(datos: CanchaCreate, service: CanchaService = Depends(get_cancha_service)):
    return service.crear_cancha(datos)


@router.get("/", response_model=list[CanchaResponse], dependencies=[con_sesion])
def obtener_todas(solo_activas: bool = True, service: CanchaService = Depends(get_cancha_service)):
    """Lista las canchas activas; solo_activas=false incluye las inhabilitadas."""
    return service.obtener_todas(solo_activas)


@router.get("/{id_cancha}", response_model=CanchaResponse, dependencies=[con_sesion])
def obtener_por_id(id_cancha: int = Path(gt=0), service: CanchaService = Depends(get_cancha_service)):
    return service.obtener_por_id(id_cancha)


@router.get("/{id_cancha}/agenda", response_model=list[PartidoResponse], dependencies=[con_sesion])
def obtener_agenda(
    fecha: date,
    id_cancha: int = Path(gt=0),
    service: CanchaService = Depends(get_cancha_service),
):
    """Partidos de la cancha en un día (?fecha=2026-12-05), para el personal de logística."""
    return service.obtener_agenda(id_cancha, fecha)


@router.patch("/{id_cancha}", response_model=CanchaResponse, dependencies=[solo_admin])
def actualizar_detalles(
    datos: CanchaUpdate,
    id_cancha: int = Path(gt=0),
    service: CanchaService = Depends(get_cancha_service),
):
    return service.actualizar_detalles(id_cancha, datos)


@router.patch("/{id_cancha}/estado", response_model=CanchaResponse, dependencies=[solo_admin])
def modificar_estado(
    datos: CanchaEstadoUpdate,
    id_cancha: int = Path(gt=0),
    service: CanchaService = Depends(get_cancha_service),
):
    """Inhabilita o rehabilita una cancha sin borrar su historial."""
    return service.modificar_estado(id_cancha, datos.estado_activo)
