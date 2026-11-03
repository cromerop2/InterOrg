"""Importa todos los modelos para resolver sus claves foráneas al crear tablas."""
from app.models.usuario_model import UsuarioModel, AdministradorModel, EntrenadorModel, ArbitroModel
from app.models.colegio_model import ColegioModel
from app.models.torneo_model import TorneoModel
from app.models.equipo_model import EquipoModel
from app.models.jugador_model import JugadorModel
from app.models.inscripcion_model import InscripcionModel
from app.models.fase_model import FaseModel
from app.models.grupo_model import GrupoModel
from app.models.partido_model import PartidoModel
from app.models.sesion_model import SesionModel
