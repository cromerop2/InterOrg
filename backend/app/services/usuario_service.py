from fastapi import HTTPException, status
from typing import List
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.usuario_schema import UsuarioCreate
from app.models.usuario_model import UsuarioModel

class UsuarioService:
    def __init__(self, repository: UsuarioRepository):
        self.repository = repository

    def crear_usuario(self, usuario_data: UsuarioCreate) -> UsuarioModel:
        """Regla de negocio: Validar que el correo no esté registrado previamente."""
        usuario_existente = self.repository.obtener_por_email(usuario_data.email)
        if usuario_existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El correo electrónico ya se encuentra registrado en el sistema."
            )
        
        return self.repository.crear(usuario_data)

    def obtener_por_id(self, usuario_id: int) -> UsuarioModel:
        """Busca un usuario por su ID y maneja el error 404 si no existe."""
        usuario = self.repository.obtener_por_id(usuario_id)
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El usuario solicitado no existe."
            )
        return usuario

    def obtener_todos(self, skip: int = 0, limit: int = 100) -> List[UsuarioModel]:
        """Obtiene la lista paginada de usuarios."""
        return self.repository.obtener_todos(skip=skip, limit=limit)