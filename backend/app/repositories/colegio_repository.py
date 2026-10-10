"""Operaciones de persistencia: consulta y guarda colegios mediante SQLAlchemy."""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.colegio_model import ColegioModel
from app.schemas.colegio_schema import ColegioCreate, ColegioUpdate


class ColegioRepository:
    """Agrupa el acceso a la BD; el servicio decide las respuestas de negocio."""

    def __init__(self, db: Session):
        # Usa la sesión entregada por get_db para esta petición.
        self.db = db

    def crear_colegio(self, datos_colegio: ColegioCreate) -> ColegioModel:
        """Convierte los datos validados en un registro y lo guarda."""
        # model_dump transforma el esquema Pydantic en un diccionario de campos.
        colegio = ColegioModel(**datos_colegio.model_dump())
        self.db.add(colegio)
        self._guardar(colegio)
        return colegio

    def obtener_por_id(self, id_colegio: int) -> ColegioModel | None:
        """Busca por clave primaria; devuelve None cuando no existe."""
        return self.db.get(ColegioModel, id_colegio)

    def obtener_todos(self, activos_solamente: bool = True) -> list[ColegioModel]:
        """Lista colegios, filtrando activos por defecto y ordenando por ID."""
        consulta = self.db.query(ColegioModel)
        if activos_solamente:
            consulta = consulta.filter(ColegioModel.estado_activo.is_(True))
        return consulta.order_by(ColegioModel.id).all()

    def actualizar_detalles(self, id_colegio: int, datos: ColegioUpdate) -> ColegioModel | None:
        """Modifica un colegio existente; devuelve None si no encuentra su ID."""
        colegio = self.obtener_por_id(id_colegio)
        if colegio is None:
            return None
        # exclude_unset evita sobrescribir campos que el usuario no envió.
        # Un correo enviado explícitamente como null sí se actualiza a None.
        for campo, valor in datos.model_dump(exclude_unset=True).items():
            setattr(colegio, campo, valor)
        self._guardar(colegio)
        return colegio

    def obtener_por_nombre(self, nombre: str) -> ColegioModel | None:
        """Consulta auxiliar para comprobar la unicidad del nombre."""
        return self.db.query(ColegioModel).filter(ColegioModel.nombre == nombre).first()

    def _guardar(self, colegio: ColegioModel) -> None:
        """Confirma los cambios y recupera los valores guardados por la BD."""
        try:
            # commit confirma la transacción (INSERT o UPDATE pendiente).
            self.db.commit()
        except IntegrityError:
            # Un conflicto, por ejemplo de nombre único, invalida la transacción.
            # rollback la revierte y permite seguir utilizando la sesión.
            self.db.rollback()
            raise
        # refresh recupera los valores definitivos, incluido el ID al crear.
        self.db.refresh(colegio)
