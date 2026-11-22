"""Reglas de negocio de pagos: el entrenador reporta, el administrador valida."""

from fastapi import HTTPException, status

from app.core.enums import EstadoInscripcionEnum, EstadoPagoEnum, EstadoTorneoEnum
from app.core.permisos import exigir_acceso_a_equipo
from app.models.pago_model import PagoModel
from app.repositories.equipo_repository import EquipoRepository
from app.repositories.pago_repository import PagoRepository
from app.repositories.torneo_repository import TorneoRepository
from app.schemas.pago_schema import PagoCreate
from app.services.equipo_service import EquipoService


class PagoService:
    def __init__(
        self,
        repository: PagoRepository,
        equipo_repository: EquipoRepository,
        torneo_repository: TorneoRepository,
        equipo_service: EquipoService,
    ):
        self.repository = repository
        self.equipo_repository = equipo_repository
        self.torneo_repository = torneo_repository
        self.equipo_service = equipo_service

    def registrar_comprobante(self, id_equipo: int, datos_pago: PagoCreate, entrenador) -> PagoModel:
        """El entrenador reporta un pago; el equipo pasa de "Preinscrito" a "Pago_Pendiente"."""
        equipo = self.equipo_service.obtener_equipo(id_equipo)
        exigir_acceso_a_equipo(entrenador, equipo, solo_dueno=True)

        if equipo.estado_inscripcion in (
            EstadoInscripcionEnum.HABILITADO,
            EstadoInscripcionEnum.DESCALIFICADO,
        ):
            raise HTTPException(
                status.HTTP_409_CONFLICT, f"El equipo ya está {equipo.estado_inscripcion.value}."
            )
        torneo = self.torneo_repository.obtener_por_id(equipo.torneo_id)
        if torneo.estado != EstadoTorneoEnum.INSCRIPCIONES:
            raise HTTPException(
                status.HTTP_409_CONFLICT, "El torneo ya no recibe pagos de inscripción."
            )
        # Una misma referencia bancaria no puede respaldar dos pagos vigentes.
        if datos_pago.referencia_transaccion and self.repository.obtener_por_referencia(
            datos_pago.referencia_transaccion
        ):
            raise HTTPException(
                status.HTTP_409_CONFLICT, "Esa referencia de transacción ya fue registrada."
            )

        pago = self.repository.crear_pago(equipo.id, datos_pago)
        if equipo.estado_inscripcion == EstadoInscripcionEnum.PREINSCRITO:
            self.equipo_repository.actualizar_estado(equipo.id, EstadoInscripcionEnum.PAGO_PENDIENTE)
        return pago

    def validar_pago(self, id_pago: int, aprobado: bool, observaciones: str | None = None) -> PagoModel:
        """Exclusivo del Administrador.

        Aprobar equivale a auditar la inscripción: exige plantilla completa y habilita el equipo.
        Rechazar guarda el motivo y, si no quedan otros pagos pendientes, devuelve el equipo a "Preinscrito".
        """
        pago = self.obtener_pago(id_pago)
        if pago.estado != EstadoPagoEnum.PENDIENTE:
            raise HTTPException(status.HTTP_409_CONFLICT, "Ese pago ya fue revisado.")

        if aprobado:
            self.equipo_service.auditar_inscripcion_equipo(pago.equipo_id, pago.id)
            return self.obtener_pago(pago.id)

        equipo = self.equipo_service.obtener_equipo(pago.equipo_id)
        otros_pendientes = any(
            otro.id != pago.id and otro.estado == EstadoPagoEnum.PENDIENTE
            for otro in self.repository.obtener_por_equipo(equipo.id)
        )
        if equipo.estado_inscripcion == EstadoInscripcionEnum.PAGO_PENDIENTE and not otros_pendientes:
            self.repository.actualizar_estado(
                pago.id, EstadoPagoEnum.RECHAZADO, observaciones, confirmar=False
            )
            # Comparten sesión: este commit guarda también el rechazo del pago.
            self.equipo_repository.actualizar_estado(equipo.id, EstadoInscripcionEnum.PREINSCRITO)
        else:
            self.repository.actualizar_estado(pago.id, EstadoPagoEnum.RECHAZADO, observaciones)
        return self.obtener_pago(pago.id)

    # ---------- consultas ----------
    def obtener_pago(self, id_pago: int) -> PagoModel:
        pago = self.repository.obtener_por_id(id_pago)
        if pago is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "El pago solicitado no existe.")
        return pago

    def obtener_por_id(self, id_pago: int, usuario) -> PagoModel:
        pago = self.obtener_pago(id_pago)
        exigir_acceso_a_equipo(usuario, self.equipo_service.obtener_equipo(pago.equipo_id))
        return pago

    def obtener_por_equipo(self, id_equipo: int, usuario) -> list[PagoModel]:
        equipo = self.equipo_service.obtener_equipo(id_equipo)
        exigir_acceso_a_equipo(usuario, equipo)
        return self.repository.obtener_por_equipo(equipo.id)

    def obtener_todos(self, estado: EstadoPagoEnum | None = None) -> list[PagoModel]:
        return self.repository.obtener_todos(estado)
