"""API de campeonatos: lecturas públicas para móvil y mutaciones administrativas."""
from typing import Literal
from fastapi import APIRouter, Depends, Path, Query, Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.security import exigir_administrador
from app.repositories.campeonato_repository import CampeonatoRepository
from app.services.campeonato_service import CampeonatoService
from app.schemas.campeonato_schema import (
    TorneoCreate, TorneoResponse, InscripcionCreate, InscripcionResponse,
    PartidoResponse, GrupoResponse, SeguimientoResponse, ProgramacionUpdate, ResultadoUpdate,
)

router = APIRouter(tags=["Campeonatos"])
admin = [Depends(exigir_administrador)]


def get_service(db: Session = Depends(get_db)):
    return CampeonatoService(CampeonatoRepository(db))


@router.post("/torneos/", response_model=TorneoResponse, status_code=201, dependencies=admin)
def crear_torneo(datos: TorneoCreate, service: CampeonatoService = Depends(get_service)):
    return service.crear_torneo(datos)


@router.get("/torneos/", response_model=list[TorneoResponse])
def obtener_torneos(estado: Literal["Inscripciones", "En_Curso", "Finalizado", "Cancelado"] | None = None,
                    service: CampeonatoService = Depends(get_service)):
    return service.obtener_torneos(estado)


@router.get("/torneos/{id_torneo}", response_model=TorneoResponse)
def obtener_torneo(id_torneo: int = Path(..., gt=0), service: CampeonatoService = Depends(get_service)):
    return service.obtener_torneo(id_torneo)


@router.post("/torneos/{id_torneo}/equipos", response_model=InscripcionResponse, status_code=201, dependencies=admin)
def inscribir_equipo(datos: InscripcionCreate, id_torneo: int = Path(..., gt=0), service: CampeonatoService = Depends(get_service)):
    return service.inscribir_equipo(id_torneo, datos)


@router.get("/torneos/{id_torneo}/equipos", response_model=list[InscripcionResponse])
def obtener_inscripciones(id_torneo: int = Path(..., gt=0), service: CampeonatoService = Depends(get_service)):
    return service.obtener_inscripciones(id_torneo)


@router.delete("/torneos/{id_torneo}/equipos/{id_equipo}", status_code=204, dependencies=admin)
def retirar_equipo(id_torneo: int = Path(..., gt=0), id_equipo: int = Path(..., gt=0), service: CampeonatoService = Depends(get_service)):
    service.retirar_equipo(id_torneo, id_equipo)
    return Response(status_code=204)


@router.post("/torneos/{id_torneo}/fixture", response_model=list[PartidoResponse], status_code=201, dependencies=admin)
def generar_fixture(id_torneo: int = Path(..., gt=0), service: CampeonatoService = Depends(get_service)):
    """Genera grupos equilibrados y todos contra todos a una vuelta por grupo."""
    return service.generar_fixture(id_torneo)


@router.get("/torneos/{id_torneo}/fixture", response_model=list[PartidoResponse])
def obtener_fixture(id_torneo: int = Path(..., gt=0), equipo_id: int | None = Query(None, gt=0),
                    fase_id: int | None = Query(None, gt=0), service: CampeonatoService = Depends(get_service)):
    """El jugador puede filtrar por su equipo sin iniciar sesión."""
    return service.obtener_fixture(id_torneo, equipo_id, fase_id)


@router.get("/torneos/{id_torneo}/posiciones", response_model=list[GrupoResponse])
def obtener_posiciones(id_torneo: int = Path(..., gt=0), service: CampeonatoService = Depends(get_service)):
    """3 puntos por victoria, 1 por empate; desempates descritos en cada grupo."""
    return service.obtener_posiciones(id_torneo)


@router.post("/torneos/{id_torneo}/avanzar", response_model=list[PartidoResponse], status_code=201, dependencies=admin)
def avanzar_fase(id_torneo: int = Path(..., gt=0), service: CampeonatoService = Depends(get_service)):
    """Genera la siguiente ronda solo cuando la actual tenga todos sus resultados."""
    return service.avanzar_fase(id_torneo)


@router.get("/torneos/{id_torneo}/seguimiento", response_model=SeguimientoResponse)
def obtener_seguimiento(id_torneo: int = Path(..., gt=0), service: CampeonatoService = Depends(get_service)):
    return service.obtener_seguimiento(id_torneo)


@router.patch("/partidos/{id_partido}/programacion", response_model=PartidoResponse, dependencies=admin)
def programar_partido(datos: ProgramacionUpdate, id_partido: int = Path(..., gt=0), service: CampeonatoService = Depends(get_service)):
    return service.programar_partido(id_partido, datos)


@router.put("/partidos/{id_partido}/resultado", response_model=PartidoResponse, dependencies=admin)
def registrar_resultado(datos: ResultadoUpdate, id_partido: int = Path(..., gt=0), service: CampeonatoService = Depends(get_service)):
    """Permite corregir resultados mientras no se haya creado una fase dependiente."""
    return service.registrar_resultado(id_partido, datos)
