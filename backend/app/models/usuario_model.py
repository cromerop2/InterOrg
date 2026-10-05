from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
from app.core.enums import RolEnum

# Tabla Base / Padre
class UsuarioModel(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre_completo = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    telefono_contacto = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    rol = Column(SQLEnum(RolEnum), nullable=False)
    estado_activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())

    # Configuración de polimorfismo para SQLAlchemy
    __mapper_args__ = {
        "polymorphic_on": rol,
        "polymorphic_identity": "usuario"
    }

# Entidad hija: Administrador
class AdministradorModel(UsuarioModel):
    __tablename__ = "administradores"

    id = Column(Integer, ForeignKey("usuarios.id"), primary_key=True)
    nivel_acceso = Column(String, nullable=False, default="Total")

    __mapper_args__ = {
        "polymorphic_identity": RolEnum.ADMINISTRADOR,
    }

# Entidad hija: Entrenador (vinculado a un colegio opcionalmente)
class EntrenadorModel(UsuarioModel):
    __tablename__ = "entrenadores"

    id = Column(Integer, ForeignKey("usuarios.id"), primary_key=True)
    #colegio_id = Column(Integer, ForeignKey("colegios.id"), nullable=True)

    # Relación con equipos a su cargo
    #equipos = relationship("EquipoModel", back_populates="entrenador")

    __mapper_args__ = {
        "polymorphic_identity": RolEnum.ENTRENADOR,
    }

# Entidad hija: Árbitro
class ArbitroModel(UsuarioModel):
    __tablename__ = "arbitros"

    id = Column(Integer, ForeignKey("usuarios.id"), primary_key=True)
    numero_colegiado = Column(String, unique=True, nullable=False)

    __mapper_args__ = {
        "polymorphic_identity": RolEnum.ARBITRO,
    }