"""Endpoints de pagos: el Entrenador reporta; el Administrador valida."""

from fastapi import APIRouter, Depends, Path, status

from app.core.dependencies import get_pago_service, obtener_usuario_actual, requerir_roles
from app.core.enums import EstadoPagoEnum, RolEnum
from app.models.usuario_model import UsuarioModel
from app.schemas.pago_schema import PagoCreate, PagoResponse, PagoValidacion
from app.services.pago_service import PagoService

router = APIRouter(tags=["Pagos"])

solo_admin = Depends(requerir_roles(RolEnum.ADMINISTRADOR))


@router.post("/equipos/{id_equipo}/pagos", response_model=PagoResponse, status_code=status.HTTP_201_CREATED)
def cargar_comprobante_pago(
    datos: PagoCreate,
    id_equipo: int = Path(gt=0),
    entrenador: UsuarioModel = Depends(requerir_roles(RolEnum.ENTRENADOR)),
    service: PagoService = Depends(get_pago_service),
):
    """El Entrenador dueño reporta un pago; el Administrador lo valida después."""
    return service.registrar_comprobante(id_equipo, datos, entrenador)


@router.get("/equipos/{id_equipo}/pagos", response_model=list[PagoResponse])
def obtener_pagos_del_equipo(
    id_equipo: int = Path(gt=0),
    usuario: UsuarioModel = Depends(obtener_usuario_actual),
    service: PagoService = Depends(get_pago_service),
):
    return service.obtener_por_equipo(id_equipo, usuario)


@router.get("/pagos/", response_model=list[PagoResponse], dependencies=[solo_admin])
def obtener_todos(estado: EstadoPagoEnum | None = None, service: PagoService = Depends(get_pago_service)):
    """Para el Administrador: p. ej. ?estado=Pendiente muestra los pagos por revisar."""
    return service.obtener_todos(estado)


@router.get("/pagos/{id_pago}", response_model=PagoResponse)
def obtener_por_id(
    id_pago: int = Path(gt=0),
    usuario: UsuarioModel = Depends(obtener_usuario_actual),
    service: PagoService = Depends(get_pago_service),
):
    return service.obtener_por_id(id_pago, usuario)


@router.patch("/pagos/{id_pago}/validar", response_model=PagoResponse, dependencies=[solo_admin])
def validar_pago(
    datos: PagoValidacion,
    id_pago: int = Path(gt=0),
    service: PagoService = Depends(get_pago_service),
):
    """Aprobar habilita el equipo (si su plantilla está completa); rechazar exige observaciones."""
    return service.validar_pago(id_pago, datos.aprobado, datos.observaciones)
