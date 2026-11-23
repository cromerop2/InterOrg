"""El día del partido: el árbitro inicia, registra eventos y marcador y cierra el acta; el administrador decreta W.O."""

from fastapi import APIRouter, Depends, Path, Query, Response, status

from app.core.dependencies import get_evento_service, get_juego_service, requerir_roles
from app.core.enums import RolEnum
from app.models.usuario_model import UsuarioModel
from app.schemas.evento_partido_schema import EventoPartidoCreate, EventoPartidoResponse, GoleadorResponse
from app.schemas.marcador_schema import MarcadorResponse, MarcadorUpdate
from app.schemas.partido_schema import PartidoResponse, PartidoWalkover
from app.services.evento_partido_service import EventoPartidoService
from app.services.juego_service import JuegoService

router = APIRouter(tags=["Juego"])

solo_admin = Depends(requerir_roles(RolEnum.ADMINISTRADOR))
solo_arbitro = Depends(requerir_roles(RolEnum.ARBITRO))


@router.post("/partidos/{id_partido}/iniciar", response_model=PartidoResponse)
def iniciar_partido(
    id_partido: int = Path(gt=0),
    arbitro: UsuarioModel = solo_arbitro,
    service: JuegoService = Depends(get_juego_service),
):
    """Solo el árbitro designado, y con la alineación de ambos equipos enviada."""
    return service.iniciar_partido(id_partido, arbitro)


@router.put("/partidos/{id_partido}/marcador", response_model=MarcadorResponse)
def registrar_marcador(
    datos: MarcadorUpdate,
    id_partido: int = Path(gt=0),
    arbitro: UsuarioModel = solo_arbitro,
    service: JuegoService = Depends(get_juego_service),
):
    return service.registrar_marcador(id_partido, datos, arbitro)


@router.post("/partidos/{id_partido}/cerrar", response_model=PartidoResponse)
def cerrar_acta_oficial(
    id_partido: int = Path(gt=0),
    arbitro: UsuarioModel = solo_arbitro,
    service: JuegoService = Depends(get_juego_service),
):
    """Cierra el acta: el partido queda Finalizado y la tabla de posiciones se actualiza."""
    return service.cerrar_acta_oficial(id_partido, arbitro)


@router.post("/partidos/{id_partido}/walkover", response_model=PartidoResponse, dependencies=[solo_admin])
def aplicar_walkover(
    datos: PartidoWalkover,
    id_partido: int = Path(gt=0),
    service: JuegoService = Depends(get_juego_service),
):
    """Decreta W.O. a favor del equipo presente (partido Programado)."""
    return service.aplicar_walkover(id_partido, datos.equipo_ganador_id)


# ---------- eventos ----------
@router.post("/partidos/{id_partido}/eventos", response_model=EventoPartidoResponse, status_code=status.HTTP_201_CREATED)
def registrar_incidencia(
    datos: EventoPartidoCreate,
    id_partido: int = Path(gt=0),
    arbitro: UsuarioModel = solo_arbitro,
    service: EventoPartidoService = Depends(get_evento_service),
):
    """Gol, asistencia, tarjeta, sustitución o autogol, validado contra la alineación oficial."""
    return service.registrar_incidencia(id_partido, datos, arbitro)


@router.get("/partidos/{id_partido}/eventos", response_model=list[EventoPartidoResponse])
def obtener_eventos(id_partido: int = Path(gt=0), service: EventoPartidoService = Depends(get_evento_service)):
    """El minuto a minuto del partido (público)."""
    return service.obtener_por_partido(id_partido)


@router.delete("/partidos/{id_partido}/eventos/{id_evento}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_evento(
    id_partido: int = Path(gt=0),
    id_evento: int = Path(gt=0),
    arbitro: UsuarioModel = solo_arbitro,
    service: EventoPartidoService = Depends(get_evento_service),
):
    """Borra un evento registrado por error y revierte su efecto (marcador o sanción)."""
    service.eliminar_evento(id_partido, id_evento, arbitro)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/torneos/{id_torneo}/goleadores", response_model=list[GoleadorResponse])
def obtener_goleadores(
    id_torneo: int = Path(gt=0),
    limite: int = Query(10, ge=1, le=100),
    service: EventoPartidoService = Depends(get_evento_service),
):
    """Tabla de goleadores con los partidos Finalizados (público). Los autogoles no cuentan."""
    return service.obtener_goleadores(id_torneo, limite)
