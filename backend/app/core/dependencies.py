"""Dependencias compartidas de FastAPI: servicios, usuario autenticado y control de roles."""

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.enums import RolEnum
from app.core.security import decodificar_token
from app.database import get_db
from app.models.usuario_model import UsuarioModel
from app.repositories.alineacion_repository import AlineacionRepository
from app.repositories.cancha_repository import CanchaRepository
from app.repositories.colegio_repository import ColegioRepository
from app.repositories.equipo_repository import EquipoRepository
from app.repositories.evento_partido_repository import EventoPartidoRepository
from app.repositories.fase_repository import FaseRepository
from app.repositories.fila_posicion_repository import FilaPosicionRepository
from app.repositories.jugador_repository import JugadorRepository
from app.repositories.marcador_repository import MarcadorRepository
from app.repositories.pago_repository import PagoRepository
from app.repositories.partido_repository import PartidoRepository
from app.repositories.tabla_posiciones_repository import TablaPosicionesRepository
from app.repositories.torneo_repository import TorneoRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.services.alineacion_service import AlineacionService
from app.services.cancha_service import CanchaService
from app.services.equipo_service import EquipoService
from app.services.evento_partido_service import EventoPartidoService
from app.services.fase_service import FaseService
from app.services.fila_posicion_service import FilaPosicionService
from app.services.juego_service import JuegoService
from app.services.marcador_service import MarcadorService
from app.services.jugador_service import JugadorService
from app.services.pago_service import PagoService
from app.services.partido_service import PartidoService
from app.services.tabla_posiciones_service import TablaPosicionesService
from app.services.usuario_service import UsuarioService

# auto_error=False: la falta de token se responde con nuestro propio 401.
esquema_bearer = HTTPBearer(auto_error=False, description="Pega aquí el access_token de /auth/login")


def _no_autenticado() -> HTTPException:
    return HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        "No autenticado o sesión inválida.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_usuario_service(db: Session = Depends(get_db)) -> UsuarioService:
    return UsuarioService(UsuarioRepository(db), ColegioRepository(db))


def _armar_equipo_service(db: Session) -> EquipoService:
    return EquipoService(
        EquipoRepository(db),
        TorneoRepository(db),
        ColegioRepository(db),
        JugadorRepository(db),
        PagoRepository(db),
        FilaPosicionRepository(db),
    )


def get_equipo_service(db: Session = Depends(get_db)) -> EquipoService:
    return _armar_equipo_service(db)


def get_jugador_service(db: Session = Depends(get_db)) -> JugadorService:
    return JugadorService(JugadorRepository(db), EquipoRepository(db), TorneoRepository(db))


def get_pago_service(db: Session = Depends(get_db)) -> PagoService:
    # Los repositorios comparten la sesión de la petición, así sus cambios se guardan en un solo commit.
    return PagoService(
        PagoRepository(db), EquipoRepository(db), TorneoRepository(db), _armar_equipo_service(db)
    )


def get_partido_service(db: Session = Depends(get_db)) -> PartidoService:
    return PartidoService(
        PartidoRepository(db),
        MarcadorRepository(db),
        FaseRepository(db),
        TorneoRepository(db),
        EquipoRepository(db),
        TablaPosicionesRepository(db),
        UsuarioRepository(db),
        CanchaService(CanchaRepository(db), PartidoRepository(db)),
    )


def get_alineacion_service(db: Session = Depends(get_db)) -> AlineacionService:
    return AlineacionService(
        AlineacionRepository(db),
        PartidoRepository(db),
        EquipoRepository(db),
        JugadorRepository(db),
        FaseRepository(db),
        TorneoRepository(db),
    )


def _armar_tabla_service(db: Session) -> TablaPosicionesService:
    return TablaPosicionesService(
        TablaPosicionesRepository(db),
        FilaPosicionRepository(db),
        FaseRepository(db),
        TorneoRepository(db),
        EquipoRepository(db),
        PartidoRepository(db),
        MarcadorRepository(db),
    )


def get_tabla_service(db: Session = Depends(get_db)) -> TablaPosicionesService:
    return _armar_tabla_service(db)


def get_fase_service(db: Session = Depends(get_db)) -> FaseService:
    return FaseService(
        FaseRepository(db),
        TorneoRepository(db),
        TablaPosicionesRepository(db),
        PartidoRepository(db),
        MarcadorRepository(db),
        _armar_tabla_service(db),
    )


def _armar_marcador_service(db: Session) -> MarcadorService:
    return MarcadorService(MarcadorRepository(db), PartidoRepository(db), FaseRepository(db))


def get_evento_service(db: Session = Depends(get_db)) -> EventoPartidoService:
    return EventoPartidoService(
        EventoPartidoRepository(db),
        PartidoRepository(db),
        AlineacionRepository(db),
        JugadorRepository(db),
        FaseRepository(db),
        TorneoRepository(db),
        _armar_marcador_service(db),
    )


def get_juego_service(db: Session = Depends(get_db)) -> JuegoService:
    return JuegoService(
        PartidoRepository(db),
        _armar_marcador_service(db),
        get_alineacion_service(db),
        FaseRepository(db),
        TorneoRepository(db),
        TablaPosicionesRepository(db),
        FilaPosicionService(FilaPosicionRepository(db)),
    )


def obtener_usuario_actual(
    credenciales: HTTPAuthorizationCredentials | None = Depends(esquema_bearer),
    db: Session = Depends(get_db),
) -> UsuarioModel:
    """Lee el JWT de la cabecera Authorization y devuelve el usuario (activo) al que pertenece."""
    if credenciales is None:
        raise _no_autenticado()
    try:
        payload = decodificar_token(credenciales.credentials)
        id_usuario = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise _no_autenticado()

    # Se consulta la BD en cada petición: si la cuenta se suspende, el token deja de servir al instante.
    usuario = UsuarioRepository(db).obtener_por_id(id_usuario)
    if usuario is None or not usuario.estado_activo:
        raise _no_autenticado()
    return usuario


def requerir_roles(*roles_permitidos: RolEnum):
    """Fábrica de dependencias: exige sesión válida y que el rol del usuario esté permitido.

    Uso:  usuario: UsuarioModel = Depends(requerir_roles(RolEnum.ADMINISTRADOR))
    """

    def dependencia(usuario: UsuarioModel = Depends(obtener_usuario_actual)) -> UsuarioModel:
        # El rol se toma de la BD, no del token, para que un cambio de rol aplique de inmediato.
        if usuario.rol not in roles_permitidos:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "No tienes permisos para esta acción.")
        return usuario

    return dependencia
