"""Endpoints de gestión de usuarios (cuentas de Administrador, Entrenador y Árbitro)."""

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from app.core.dependencies import get_usuario_service, obtener_usuario_actual, requerir_roles
from app.core.enums import RolEnum
from app.models.usuario_model import UsuarioModel
from app.schemas.usuario_schema import UsuarioCreate, UsuarioEstadoUpdate, UsuarioResponse
from app.services.usuario_service import UsuarioService

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

solo_admin = Depends(requerir_roles(RolEnum.ADMINISTRADOR))


@router.post(
    "/",
    response_model=UsuarioResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[solo_admin],
)
def registrar_usuario(datos: UsuarioCreate, servicio: UsuarioService = Depends(get_usuario_service)):
    """Solo un Administrador crea cuentas. El primer administrador se crea con scripts/crear_admin.py."""
    return servicio.registrar_usuario(datos)


@router.get("/", response_model=list[UsuarioResponse], dependencies=[solo_admin])
def listar_usuarios(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    servicio: UsuarioService = Depends(get_usuario_service),
):
    return servicio.listar_usuarios(skip, limit)


@router.get("/{usuario_id}", response_model=UsuarioResponse)
def obtener_usuario(
    usuario_id: int = Path(gt=0),
    actual: UsuarioModel = Depends(obtener_usuario_actual),
    servicio: UsuarioService = Depends(get_usuario_service),
):
    """Un Administrador ve a cualquiera; los demás roles solo su propia cuenta."""
    if actual.rol != RolEnum.ADMINISTRADOR and actual.id != usuario_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "No tienes permisos para esta acción.")
    return servicio.obtener_usuario(usuario_id)


@router.patch("/{usuario_id}/estado", response_model=UsuarioResponse)
def modificar_estado(
    datos: UsuarioEstadoUpdate,
    usuario_id: int = Path(gt=0),
    actual: UsuarioModel = Depends(requerir_roles(RolEnum.ADMINISTRADOR)),
    servicio: UsuarioService = Depends(get_usuario_service),
):
    """Suspende o habilita una cuenta sin borrar su historial."""
    return servicio.modificar_estado(usuario_id, datos.estado_activo, actual.id)
