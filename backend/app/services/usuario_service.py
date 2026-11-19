"""Reglas de negocio y seguridad de los usuarios."""

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.core.security import (
    crear_token_acceso,
    hash_falso,
    hashear_password,
    verificar_password,
)
from app.models.usuario_model import UsuarioModel
from app.repositories.colegio_repository import ColegioRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.usuario_schema import TokenResponse, UsuarioCreate


class UsuarioService:
    def __init__(self, repository: UsuarioRepository, colegio_repository: ColegioRepository):
        self.repository = repository
        self.colegio_repository = colegio_repository

    def registrar_usuario(self, datos_registro: UsuarioCreate) -> UsuarioModel:
        """Valida unicidad y referencias, encripta la contraseña y delega el guardado al repositorio."""
        if self.repository.obtener_por_email(datos_registro.email):
            raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe un usuario con ese correo.")

        if datos_registro.rol == "Entrenador" and datos_registro.colegio_id is not None:
            colegio = self.colegio_repository.obtener_por_id(datos_registro.colegio_id)
            if colegio is None:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "El colegio indicado no existe.")
            if not colegio.estado_activo:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, "El colegio indicado está inactivo.")

        if datos_registro.rol == "Arbitro" and datos_registro.numero_colegiado is not None:
            if self.repository.obtener_por_numero_colegiado(datos_registro.numero_colegiado):
                raise HTTPException(
                    status.HTTP_409_CONFLICT, "Ya existe un árbitro con ese número de colegiado."
                )

        try:
            password_hash = hashear_password(datos_registro.password)
        except ValueError as error:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(error))

        try:
            return self.repository.crear(datos_registro, password_hash)
        except IntegrityError:
            # Carrera entre dos peticiones simultáneas con el mismo correo o número de colegiado.
            raise HTTPException(
                status.HTTP_409_CONFLICT, "El correo o el número de colegiado ya están registrados."
            )

    def autenticar_usuario(self, email: str, password_plana: str) -> TokenResponse:
        """Valida credenciales y cuenta activa; devuelve el JWT. Siempre el mismo 401 si algo falla."""
        usuario = self.repository.obtener_por_email(email)
        # Si el correo no existe se verifica contra un hash falso para no revelar (por tiempo) qué correos existen.
        hash_guardado = usuario.password_hash if usuario else hash_falso()
        password_correcta = verificar_password(password_plana, hash_guardado)

        if usuario is None or not password_correcta or not usuario.estado_activo:
            raise HTTPException(
                status.HTTP_401_UNAUTHORIZED,
                "Credenciales inválidas.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = crear_token_acceso(usuario.id, usuario.rol.value)
        return TokenResponse(access_token=token, rol=usuario.rol)

    def obtener_usuario(self, id_usuario: int) -> UsuarioModel:
        usuario = self.repository.obtener_por_id(id_usuario)
        if usuario is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado.")
        return usuario

    def listar_usuarios(self, skip: int = 0, limit: int = 100) -> list[UsuarioModel]:
        return self.repository.obtener_todos(skip, limit)

    def modificar_estado(self, id_usuario: int, activo: bool, id_solicitante: int) -> UsuarioModel:
        """Suspende o habilita una cuenta. Un administrador no puede suspenderse a sí mismo."""
        if id_usuario == id_solicitante and not activo:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "No puedes suspender tu propia cuenta.")
        usuario = self.repository.modificar_estado(id_usuario, activo)
        if usuario is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado.")
        return usuario
