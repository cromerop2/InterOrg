"""Control de acceso a recursos de un equipo: su entrenador o un Administrador."""

from fastapi import HTTPException, status

from app.core.enums import RolEnum


def exigir_acceso_a_equipo(usuario, equipo, solo_dueno: bool = False) -> None:
    """Lanza 403 si el usuario no puede ver el equipo (o modificarlo, con solo_dueno=True).

    - Lectura: el Administrador o el Entrenador dueño del equipo.
    - Escritura (solo_dueno=True): únicamente el Entrenador dueño.
    """
    es_dueno = usuario.rol == RolEnum.ENTRENADOR and equipo.entrenador_id == usuario.id
    if es_dueno or (not solo_dueno and usuario.rol == RolEnum.ADMINISTRADOR):
        return
    raise HTTPException(status.HTTP_403_FORBIDDEN, "No tienes permisos sobre este equipo.")
