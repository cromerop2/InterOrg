"""Recibe peticiones HTTP de Colegio y delega su procesamiento al servicio."""

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.orm import Session

from app.core.dependencies import (
    get_equipo_service,
    get_usuario_service,
    obtener_usuario_actual,
    requerir_roles,
)
from app.core.enums import RolEnum
from app.database import get_db
from app.repositories.colegio_repository import ColegioRepository
from app.schemas.colegio_schema import ColegioCreate, ColegioResponse, ColegioUpdate
from app.schemas.equipo_schema import EquipoResponse
from app.schemas.usuario_schema import UsuarioResponse
from app.services.colegio_service import ColegioService
from app.services.equipo_service import EquipoService
from app.services.usuario_service import UsuarioService


# Todas las rutas empiezan por /colegios y aparecen bajo Colegios en Swagger.
router = APIRouter(prefix="/colegios", tags=["Colegios"])

# Consultar: cualquier usuario con sesión. Crear y modificar: solo el Administrador.
solo_admin = Depends(requerir_roles(RolEnum.ADMINISTRADOR))
con_sesion = Depends(obtener_usuario_actual)


def get_colegio_service(db: Session = Depends(get_db)) -> ColegioService:
    """Conecta sesión, repositorio y servicio para atender la petición."""
    # Depends solicita la sesión a get_db, que también se encarga de cerrarla.
    return ColegioService(ColegioRepository(db))


# response_model define los campos de salida; 201 indica creación exitosa.
@router.post("/", response_model=ColegioResponse, status_code=status.HTTP_201_CREATED, dependencies=[solo_admin])
def crear_colegio(
    datos_colegio: ColegioCreate,
    service: ColegioService = Depends(get_colegio_service),
):
    """POST /colegios/: valida el JSON con ColegioCreate y crea el colegio."""
    return service.crear_colegio(datos_colegio)


@router.get("/", response_model=list[ColegioResponse], dependencies=[con_sesion])
def obtener_todos(
    activos_solamente: bool = True,
    service: ColegioService = Depends(get_colegio_service),
):
    """GET /colegios/: lista activos; activos_solamente=false incluye inactivos."""
    return service.obtener_todos(activos_solamente)


@router.get("/{id_colegio}", response_model=ColegioResponse, dependencies=[con_sesion])
def obtener_por_id(
    id_colegio: int = Path(..., gt=0),
    service: ColegioService = Depends(get_colegio_service),
):
    """GET /colegios/{id_colegio}: consulta un ID; Path exige que sea positivo."""
    return service.obtener_por_id(id_colegio)


@router.patch("/{id_colegio}", response_model=ColegioResponse, dependencies=[solo_admin])
def actualizar_detalles(
    datos: ColegioUpdate,
    id_colegio: int = Path(..., gt=0),
    service: ColegioService = Depends(get_colegio_service),
):
    """PATCH /colegios/{id_colegio}: cambia solo los campos enviados, incluido estado_activo."""
    return service.actualizar_detalles(id_colegio, datos)


@router.get("/{id_colegio}/equipos", response_model=list[EquipoResponse], dependencies=[solo_admin])
def obtener_equipos_inscritos(id_colegio: int = Path(gt=0), equipos: EquipoService = Depends(get_equipo_service)):
    """Equipos del colegio en cualquier torneo."""
    return equipos.obtener_equipos_inscritos(id_colegio)


@router.put(
    "/{id_colegio}/entrenadores/{id_entrenador}", response_model=UsuarioResponse, dependencies=[solo_admin]
)
def vincular_entrenador(
    id_colegio: int = Path(gt=0),
    id_entrenador: int = Path(gt=0),
    usuarios: UsuarioService = Depends(get_usuario_service),
):
    """Enlaza a un Entrenador con el colegio que representa."""
    return usuarios.vincular_entrenador(id_colegio, id_entrenador)
