"""Contraseñas con PBKDF2 y autorización basada en sesiones Bearer revocables."""
import hashlib
import hmac
import secrets
import time
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.hash import pbkdf2_sha256
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.usuario_model import UsuarioModel
from app.models.sesion_model import SesionModel
from app.core.enums import RolEnum

bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    """Usa salt aleatorio y un coste explícito para las contraseñas nuevas."""
    return pbkdf2_sha256.using(rounds=600000).hash(password)


def verificar_password(password: str, guardada: str) -> bool:
    """Admite el hash nuevo y migra las contraseñas planas de la versión anterior."""
    if guardada.startswith("$pbkdf2-sha256$"):
        try:
            return pbkdf2_sha256.verify(password, guardada)
        except ValueError:
            return False
    # No se interpreta como texto plano un hash de un formato desconocido.
    return not guardada.startswith("$") and hmac.compare_digest(password.encode(), guardada.encode())


def crear_sesion(db: Session, usuario: UsuarioModel) -> str:
    token = secrets.token_urlsafe(32)
    db.add(SesionModel(token_hash=hashlib.sha256(token.encode()).hexdigest(),
                       usuario_id=usuario.id, expira_en=int(time.time()) + 43200))
    db.commit()
    return token


def usuario_actual(credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
                   db: Session = Depends(get_db)) -> UsuarioModel:
    """Consulta el estado y rol actuales; no confía en un rol enviado por el cliente."""
    error = HTTPException(401, "Sesión ausente, inválida o vencida.", headers={"WWW-Authenticate": "Bearer"})
    if credentials is None:
        raise error
    sesion = db.get(SesionModel, hashlib.sha256(credentials.credentials.encode()).hexdigest())
    if sesion is None or sesion.expira_en <= time.time():
        raise error
    usuario = db.get(UsuarioModel, sesion.usuario_id)
    if usuario is None or not usuario.estado_activo:
        raise error
    return usuario


def exigir_administrador(usuario: UsuarioModel = Depends(usuario_actual)) -> UsuarioModel:
    """Protege las mutaciones del campeonato frente a otros roles."""
    if usuario.rol != RolEnum.ADMINISTRADOR:
        raise HTTPException(403, "Esta operación requiere un administrador.")
    return usuario
