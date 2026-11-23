"""Endpoints de grupos y tablas de posiciones: la consulta es pública; armar grupos es del Administrador."""

from fastapi import APIRouter, Depends, Path, status

from app.core.dependencies import get_tabla_service, requerir_roles
from app.core.enums import RolEnum
from app.models.tabla_posiciones_model import TablaPosicionesModel
from app.schemas.tabla_posiciones_schema import (
    CierreGrupoResponse,
    FilaPosicionResponse,
    GruposConfiguracion,
    TablaClasificacionResponse,
    TablaPosicionesResponse,
)
from app.services.tabla_posiciones_service import TablaPosicionesService

router = APIRouter(tags=["Tablas de posiciones"])

solo_admin = Depends(requerir_roles(RolEnum.ADMINISTRADOR))


def _con_clasificacion(tabla: TablaPosicionesModel, service: TablaPosicionesService) -> TablaClasificacionResponse:
    filas = service.calcular_clasificacion_actual(tabla.id)
    return TablaClasificacionResponse(
        **TablaPosicionesResponse.model_validate(tabla).model_dump(),
        filas=[FilaPosicionResponse.model_validate(fila) for fila in filas],
    )


@router.post(
    "/fases/{id_fase}/grupos",
    response_model=list[TablaClasificacionResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[solo_admin],
)
def inicializar_grupos(
    distribucion: GruposConfiguracion,
    id_fase: int = Path(gt=0),
    service: TablaPosicionesService = Depends(get_tabla_service),
):
    """Crea los grupos de una fase de formato Grupos y matricula a sus equipos con todo en cero."""
    tablas = service.inicializar_grupos(id_fase, distribucion)
    return [_con_clasificacion(tabla, service) for tabla in tablas]


@router.get("/fases/{id_fase}/tablas", response_model=list[TablaClasificacionResponse])
def obtener_tablas_de_la_fase(id_fase: int = Path(gt=0), service: TablaPosicionesService = Depends(get_tabla_service)):
    return [_con_clasificacion(tabla, service) for tabla in service.obtener_por_fase(id_fase)]


@router.get("/tablas/{id_tabla}", response_model=TablaClasificacionResponse)
def obtener_tabla(id_tabla: int = Path(gt=0), service: TablaPosicionesService = Depends(get_tabla_service)):
    return _con_clasificacion(service.obtener_por_id(id_tabla), service)


@router.post("/tablas/{id_tabla}/reabrir", response_model=TablaClasificacionResponse, dependencies=[solo_admin])
def reabrir_grupo(id_tabla: int = Path(gt=0), service: TablaPosicionesService = Depends(get_tabla_service)):
    """Reabre un grupo cerrado para corregir un acta (mientras la fase no haya finalizado)."""
    return _con_clasificacion(service.reabrir_grupo(id_tabla), service)


@router.post("/tablas/{id_tabla}/cerrar", response_model=CierreGrupoResponse, dependencies=[solo_admin])
def auditar_y_cerrar_grupo(id_tabla: int = Path(gt=0), service: TablaPosicionesService = Depends(get_tabla_service)):
    """Cierra el grupo (todos los partidos jugados) y devuelve los equipos que clasifican."""
    tabla, clasificados = service.auditar_y_cerrar_grupo(id_tabla)
    return CierreGrupoResponse(**_con_clasificacion(tabla, service).model_dump(), clasificados=clasificados)
