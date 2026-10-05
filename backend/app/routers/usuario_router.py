from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.services.usuario_service import UsuarioService
from app.database import get_db  # Dependencia que abre y cierra la sesión de la BD
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.usuario_schema import UsuarioCreate, UsuarioResponse

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

def get_usuario_service(db: Session = Depends(get_db)) -> UsuarioService:
    repository = UsuarioRepository(db)
    return UsuarioService(repository)

@router.post("/", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def crear_usuario(usuario_data: UsuarioCreate, db: Session = Depends(get_db)):
    """
    Crea un nuevo usuario en el sistema. 
    Automáticamente detectará si es Administrador, Entrenador o Árbitro según el rol enviado.
    """
    repositorio = UsuarioRepository(db)

    # Validamos opcionalmente si el correo ya está registrado
    usuario_existente = repositorio.obtener_por_email(usuario_data.email)
    if usuario_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electrónico ya se encuentra registrado."
        )

    # Creamos el usuario a través del repositorio
    nuevo_usuario = repositorio.crear(usuario_data)
    return nuevo_usuario


@router.get("/", response_model=List[UsuarioResponse])
def obtener_usuarios(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Obtiene una lista paginada de todos los usuarios registrados en el sistema.
    """
    repositorio = UsuarioRepository(db)
    usuarios = repositorio.obtener_todos(skip=skip, limit=limit)
    return usuarios


@router.get("/{usuario_id}", response_model=UsuarioResponse)
def obtener_usuario_por_id(usuario_id: int, db: Session = Depends(get_db)):
    """
    Busca y devuelve un usuario específico filtrado por su ID único.
    """
    repositorio = UsuarioRepository(db)
    usuario = repositorio.obtener_por_id(usuario_id)
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El usuario solicitado no existe."
        )
        
    return usuario