"""Acceso a la BD para usuarios: consultas y guardado, sin reglas de negocio."""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.enums import RolEnum
from app.models.usuario_model import (
    AdministradorModel,
    ArbitroModel,
    EntrenadorModel,
    UsuarioModel,
)
from app.schemas.usuario_schema import UsuarioCreate

_MODELO_POR_ROL = {
    RolEnum.ADMINISTRADOR: AdministradorModel,
    RolEnum.ENTRENADOR: EntrenadorModel,
    RolEnum.ARBITRO: ArbitroModel,
}


class UsuarioRepository:
    def __init__(self, db: Session):
        self.db = db

    def crear(self, usuario_in: UsuarioCreate, password_hash: str) -> UsuarioModel:
        """Inserta el usuario en la tabla de su rol. Recibe el hash ya calculado, nunca la contraseña."""
        campos = usuario_in.model_dump(exclude={"password"})
        rol = RolEnum(campos.pop("rol"))
        # Un valor None no debe pisar el default del modelo (p. ej. nivel_acceso="Total").
        campos = {k: v for k, v in campos.items() if v is not None}
        # SQLAlchemy asigna la columna "rol" según la clase hija elegida.
        nuevo = _MODELO_POR_ROL[rol](**campos, password_hash=password_hash)
        self.db.add(nuevo)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise
        self.db.refresh(nuevo)
        return nuevo

    def obtener_por_email(self, email: str) -> UsuarioModel | None:
        return self.db.query(UsuarioModel).filter(UsuarioModel.email == email).first()

    def obtener_por_id(self, id_usuario: int) -> UsuarioModel | None:
        return self.db.get(UsuarioModel, id_usuario)

    def obtener_por_numero_colegiado(self, numero_colegiado: str) -> ArbitroModel | None:
        return (
            self.db.query(ArbitroModel)
            .filter(ArbitroModel.numero_colegiado == numero_colegiado)
            .first()
        )

    def obtener_todos(self, skip: int = 0, limit: int = 100) -> list[UsuarioModel]:
        return (
            self.db.query(UsuarioModel)
            .order_by(UsuarioModel.id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def modificar_estado(self, id_usuario: int, activo: bool) -> UsuarioModel | None:
        """Suspende o habilita una cuenta sin borrar su historial. None si el usuario no existe."""
        usuario = self.obtener_por_id(id_usuario)
        if usuario is None:
            return None
        usuario.estado_activo = activo
        self.db.commit()
        self.db.refresh(usuario)
        return usuario
