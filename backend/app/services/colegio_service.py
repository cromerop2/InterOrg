"""Reglas de Colegio: valida existencia y nombre único antes de guardar."""

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.models.colegio_model import ColegioModel
from app.repositories.colegio_repository import ColegioRepository
from app.schemas.colegio_schema import ColegioCreate, ColegioUpdate


class ColegioService:
    """Coordina las operaciones del repositorio y comunica errores a la API."""

    def __init__(self, repository: ColegioRepository):
        # Recibe el repositorio para mantener las consultas fuera del servicio.
        self.repository = repository

    def crear_colegio(self, datos_colegio: ColegioCreate) -> ColegioModel:
        """Comprueba que el nombre esté disponible y solicita guardar el colegio."""
        self._validar_nombre_disponible(datos_colegio.nombre)
        try:
            return self.repository.crear_colegio(datos_colegio)
        except IntegrityError:
            # Otra petición pudo registrar el mismo nombre tras la validación.
            self._validar_nombre_disponible(datos_colegio.nombre)
            raise

    def obtener_por_id(self, id_colegio: int) -> ColegioModel:
        """Devuelve el colegio o un error HTTP 404 si el ID no existe."""
        colegio = self.repository.obtener_por_id(id_colegio)
        if colegio is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El colegio solicitado no existe.",
            )
        return colegio

    def obtener_todos(self, activos_solamente: bool = True) -> list[ColegioModel]:
        """Solicita la lista respetando el filtro de colegios activos."""
        return self.repository.obtener_todos(activos_solamente)

    def actualizar_detalles(self, id_colegio: int, datos: ColegioUpdate) -> ColegioModel:
        """Verifica la existencia y, si cambia el nombre, que no esté ocupado."""
        self.obtener_por_id(id_colegio)
        if datos.nombre is not None:
            self._validar_nombre_disponible(datos.nombre, id_colegio)
        try:
            colegio = self.repository.actualizar_detalles(id_colegio, datos)
        except IntegrityError:
            # Revisa si el fallo fue un nombre ocupado por otra petición.
            # Si la causa es distinta, conserva el error original de la BD.
            if datos.nombre is not None:
                self._validar_nombre_disponible(datos.nombre, id_colegio)
            raise
        if colegio is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El colegio solicitado no existe.",
            )
        return colegio

    def _validar_nombre_disponible(self, nombre: str, id_colegio: int | None = None) -> None:
        """Devuelve 409 si otro colegio tiene el nombre, aunque esté inactivo."""
        existente = self.repository.obtener_por_nombre(nombre)
        # Al actualizar, conservar el nombre del propio colegio es válido.
        if existente is not None and existente.id != id_colegio:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un colegio con ese nombre.",
            )
