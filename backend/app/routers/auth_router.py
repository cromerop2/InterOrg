"""Inicio/cierre de sesión usados por el panel administrativo y la app móvil."""
import hashlib
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.security import bearer, usuario_actual, hash_password, verificar_password, crear_sesion
from app.models.usuario_model import UsuarioModel
from app.models.sesion_model import SesionModel
from app.schemas.usuario_schema import UsuarioResponse

router = APIRouter(prefix="/auth", tags=["Autenticación"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=1024)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 43200


@router.post("/login", response_model=TokenResponse)
def iniciar_sesion(datos: LoginRequest, db: Session = Depends(get_db)):
    """Las credenciales inválidas no revelan si una dirección de correo existe."""
    usuario = db.query(UsuarioModel).filter_by(email=datos.email).first()
    if usuario is None or not usuario.estado_activo or not verificar_password(datos.password, usuario.password_hash):
        raise HTTPException(401, "Credenciales inválidas.")
    # La actualización ocurre solo después de comprobar la contraseña anterior.
    if not usuario.password_hash.startswith("$pbkdf2-sha256$"):
        usuario.password_hash = hash_password(datos.password)
    return TokenResponse(access_token=crear_sesion(db, usuario))


@router.get("/me", response_model=UsuarioResponse)
def consultar_sesion(usuario: UsuarioModel = Depends(usuario_actual)):
    return usuario


@router.post("/logout", status_code=204)
def cerrar_sesion(usuario: UsuarioModel = Depends(usuario_actual),
                  credentials: HTTPAuthorizationCredentials = Depends(bearer),
                  db: Session = Depends(get_db)):
    sesion = db.get(SesionModel, hashlib.sha256(credentials.credentials.encode()).hexdigest())
    db.delete(sesion)
    db.commit()
    return Response(status_code=204)
