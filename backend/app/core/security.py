"""Seguridad: hash de contraseñas (bcrypt) y firma/lectura de tokens JWT."""

from datetime import datetime, timedelta, timezone
from functools import lru_cache

import bcrypt
import jwt

from app.config import settings

# bcrypt solo procesa los primeros 72 bytes; se rechaza en vez de truncar en silencio.
LIMITE_BYTES_PASSWORD = 72


def hashear_password(password_plana: str) -> str:
    """Devuelve el hash bcrypt (con sal incluida) de una contraseña en texto plano."""
    datos = password_plana.encode("utf-8")
    if len(datos) > LIMITE_BYTES_PASSWORD:
        raise ValueError(f"La contraseña no puede superar {LIMITE_BYTES_PASSWORD} bytes.")
    return bcrypt.hashpw(datos, bcrypt.gensalt()).decode("utf-8")


def verificar_password(password_plana: str, password_hash: str) -> bool:
    """Compara una contraseña con su hash; nunca lanza excepciones por datos inválidos."""
    datos = password_plana.encode("utf-8")
    if len(datos) > LIMITE_BYTES_PASSWORD:
        return False
    try:
        return bcrypt.checkpw(datos, password_hash.encode("utf-8"))
    except ValueError:
        # El valor guardado no es un hash bcrypt válido (p. ej. una contraseña vieja en texto plano).
        return False


@lru_cache(maxsize=1)
def hash_falso() -> str:
    """Hash descartable para gastar el mismo tiempo cuando el correo no existe (evita enumerar usuarios)."""
    return hashear_password("contrasena-descartable")


def crear_token_acceso(id_usuario: int, rol: str) -> str:
    """Firma un JWT con el id del usuario (sub), su rol y la fecha de expiración."""
    ahora = datetime.now(timezone.utc)
    payload = {
        "sub": str(id_usuario),  # PyJWT exige que sub sea texto
        "rol": rol,
        "iat": ahora,
        "exp": ahora + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decodificar_token(token: str) -> dict:
    """Valida firma y expiración. Lanza jwt.PyJWTError si el token no es válido."""
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],  # lista fija: no se acepta el algoritmo que declare el token
        options={"require": ["exp", "sub"]},
    )
