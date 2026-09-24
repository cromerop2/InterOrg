from app.repositories.jugador_repository import JugadorRepository
from app.schemas.jugador_schema import JugadorCreate, JugadorResponse

class JugadorService:
    def __init__(self, repository: JugadorRepository):
        self.repository = repository

    def registrar_jugador(self, jugador_in: JugadorCreate) -> JugadorResponse:
        # Aquí puedes agregar validaciones de negocio futuras (ej. verificar si la identificación ya existe)
        return self.repository.crear(jugador_in)