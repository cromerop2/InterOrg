"""Define cómo se guardan los atributos de Colegio en la base de datos."""

from sqlalchemy import Boolean, Column, Integer, String

from app.database import Base


class ColegioModel(Base):
    """Cada instancia representa una fila de la tabla colegios."""

    __tablename__ = "colegios"

    # Clave primaria: la base de datos asigna un ID al insertar el colegio.
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    # unique impide repetir nombres; index facilita buscarlos por nombre.
    nombre = Column(String, unique=True, index=True, nullable=False)
    # nullable=False obliga a guardar estos datos de ubicación y contacto.
    direccion = Column(String, nullable=False)
    representante_legal = Column(String, nullable=False)
    telefono_contacto = Column(String, nullable=False)
    # El correo puede quedar sin valor porque es un dato opcional.
    email_institucional = Column(String, nullable=True)
    # False permite desactivar un colegio conservando su registro.
    estado_activo = Column(Boolean, default=True, nullable=False)
