from sqlalchemy.orm import Session
from app.models.usuario_model import (
    UsuarioModel, 
    AdministradorModel, 
    EntrenadorModel, 
    ArbitroModel
)
from app.schemas.usuario_schema import UsuarioCreate
from app.core.enums import RolEnum

class UsuarioRepository:
    def __init__(self, db: Session):
        self.db = db

    def crear(self, usuario_data: UsuarioCreate) -> UsuarioModel:
        datos_dict = usuario_data.model_dump()
        password_plana = datos_dict.pop("password")
        rol = datos_dict.get("rol")

        # Dependiendo del rol, instanciamos el modelo hijo correspondiente
        if rol == RolEnum.ADMINISTRADOR:
            # Extraemos los campos específicos de Administrador si vienen en el schema
            nuevo_usuario = AdministradorModel(
                **datos_dict,
                password_hash=password_plana,
                nivel_acceso=datos_dict.get("nivel_acceso", "Total"),
            )
        elif rol == RolEnum.ENTRENADOR:
            nuevo_usuario = EntrenadorModel(
                **datos_dict,
                password_hash=password_plana,
                colegio_id=datos_dict.get("colegio_id")
            )
        elif rol == RolEnum.ARBITRO:
            nuevo_usuario = ArbitroModel(
                **datos_dict,
                password_hash=password_plana,
                numero_colegiado=datos_dict.get("numero_colegiado", "PENDIENTE")
            )
        else:
            # Fallback por si acaso
            nuevo_usuario = UsuarioModel(
                **datos_dict,
                password_hash=password_plana
            )

        self.db.add(nuevo_usuario)
        self.db.commit()
        self.db.refresh(nuevo_usuario)
        return nuevo_usuario

    def obtener_por_id(self, usuario_id: int) -> UsuarioModel | None:
        # SQLAlchemy es inteligente: si buscas por ID en UsuarioModel, 
        # te devolverá la instancia de Administrador, Entrenador o Árbitro según corresponda.
        return self.db.query(UsuarioModel).filter(UsuarioModel.id == usuario_id).first()

    def obtener_por_email(self, email: str) -> UsuarioModel | None:
        return self.db.query(UsuarioModel).filter(UsuarioModel.email == email).first()

    def obtener_todos(self, skip: int = 0, limit: int = 100) -> list[UsuarioModel]:
        return self.db.query(UsuarioModel).offset(skip).limit(limit).all()