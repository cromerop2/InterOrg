"""Recibe peticiones HTTP de Colegio y delega su procesamiento al servicio."""

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.colegio_repository import ColegioRepository
from app.schemas.colegio_schema import ColegioCreate, ColegioResponse, ColegioUpdate
from app.services.colegio_service import ColegioService


# Todas las rutas empiezan por /colegios y aparecen bajo Colegios en Swagger.
router = APIRouter(prefix="/colegios", tags=["Colegios"])


def get_colegio_service(db: Session = Depends(get_db)) -> ColegioService:
    """Conecta sesión, repositorio y servicio para atender la petición."""
    # Depends solicita la sesión a get_db, que también se encarga de cerrarla.
    return ColegioService(ColegioRepository(db))


# response_model define los campos de salida; 201 indica creación exitosa.
@router.post("/", response_model=ColegioResponse, status_code=status.HTTP_201_CREATED)
def crear_colegio(
    datos_colegio: ColegioCreate,
    service: ColegioService = Depends(get_colegio_service),
):
    """POST /colegios/: valida el JSON con ColegioCreate y crea el colegio."""
    return service.crear_colegio(datos_colegio)


@router.get("/", response_model=list[ColegioResponse])
def obtener_todos(
    activos_solamente: bool = True,
    service: ColegioService = Depends(get_colegio_service),
):
    """GET /colegios/: lista activos; activos_solamente=false incluye inactivos."""
    return service.obtener_todos(activos_solamente)


@router.get("/{id_colegio}", response_model=ColegioResponse)
def obtener_por_id(
    id_colegio: int = Path(..., gt=0),
    service: ColegioService = Depends(get_colegio_service),
):
    """GET /colegios/{id_colegio}: consulta un ID; Path exige que sea positivo."""
    return service.obtener_por_id(id_colegio)


@router.patch("/{id_colegio}", response_model=ColegioResponse)
def actualizar_detalles(
    datos: ColegioUpdate,
    id_colegio: int = Path(..., gt=0),
    service: ColegioService = Depends(get_colegio_service),
):
    """PATCH /colegios/{id_colegio}: cambia solo los campos enviados, incluido estado_activo."""
    return service.actualizar_detalles(id_colegio, datos)
