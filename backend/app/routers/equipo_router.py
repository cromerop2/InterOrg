"""Catálogo para móvil: lectura pública y creación exclusiva del administrador."""
from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.security import exigir_administrador
from app.repositories.equipo_repository import EquipoRepository
from app.services.equipo_service import EquipoService
from app.schemas.campeonato_schema import EquipoCreate, EquipoResponse, JugadorCreate, JugadorResponse

router = APIRouter(tags=["Equipos y jugadores"])


def get_service(db: Session = Depends(get_db)):
    return EquipoService(EquipoRepository(db))


@router.post("/equipos/", response_model=EquipoResponse, status_code=201, dependencies=[Depends(exigir_administrador)])
def crear_equipo(datos: EquipoCreate, service: EquipoService = Depends(get_service)):
    """Solo administración puede crear equipos."""
    return service.crear_equipo(datos)


@router.get("/equipos/", response_model=list[EquipoResponse])
def obtener_equipos(colegio_id: int | None = Query(None, gt=0), service: EquipoService = Depends(get_service)):
    return service.obtener_equipos(colegio_id)


@router.get("/equipos/{id_equipo}", response_model=EquipoResponse)
def obtener_equipo(id_equipo: int = Path(..., gt=0), service: EquipoService = Depends(get_service)):
    return service.obtener_equipo(id_equipo)


@router.post("/jugadores/", response_model=JugadorResponse, status_code=201, dependencies=[Depends(exigir_administrador)])
def crear_jugador(datos: JugadorCreate, service: EquipoService = Depends(get_service)):
    return service.crear_jugador(datos)


@router.get("/equipos/{id_equipo}/jugadores", response_model=list[JugadorResponse])
def obtener_jugadores(id_equipo: int = Path(..., gt=0), service: EquipoService = Depends(get_service)):
    """Omite documento de identidad y fecha de nacimiento."""
    return service.obtener_jugadores(id_equipo)
