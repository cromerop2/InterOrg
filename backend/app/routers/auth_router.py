"""Endpoints de autenticación: login y datos de la sesión actual."""

from fastapi import APIRouter, Depends

from app.core.dependencies import get_usuario_service, obtener_usuario_actual
from app.models.usuario_model import UsuarioModel
from app.schemas.usuario_schema import LoginRequest, TokenResponse, UsuarioResponse
from app.services.usuario_service import UsuarioService

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/login", response_model=TokenResponse)
def login(datos: LoginRequest, servicio: UsuarioService = Depends(get_usuario_service)):
    """Recibe correo y contraseña; devuelve el token JWT y el rol."""
    return servicio.autenticar_usuario(datos.email, datos.password)


@router.get("/me", response_model=UsuarioResponse)
def mi_perfil(usuario: UsuarioModel = Depends(obtener_usuario_actual)):
    """Devuelve los datos del usuario dueño del token."""
    return usuario
