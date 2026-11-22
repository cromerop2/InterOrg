"""Importa todos los modelos para que Base.metadata conozca cada tabla.

Al crear un modelo nuevo, agrégalo aquí; así create_all lo incluye.
"""

from app.models.cancha_model import CanchaModel
from app.models.colegio_model import ColegioModel
from app.models.equipo_model import EquipoModel
from app.models.fase_model import FaseModel
from app.models.jugador_model import JugadorModel
from app.models.pago_model import PagoModel
from app.models.torneo_model import TorneoModel
from app.models.usuario_model import (
    AdministradorModel,
    ArbitroModel,
    EntrenadorModel,
    UsuarioModel,
)

__all__ = [
    "CanchaModel",
    "ColegioModel",
    "EquipoModel",
    "FaseModel",
    "JugadorModel",
    "PagoModel",
    "TorneoModel",
    "UsuarioModel",
    "AdministradorModel",
    "EntrenadorModel",
    "ArbitroModel",
]
