"""Importa todos los modelos para que Base.metadata conozca cada tabla.

Al crear un modelo nuevo, agrégalo aquí; así create_all lo incluye.
"""

from app.models.alineacion_model import AlineacionModel
from app.models.auditoria_acta_model import AuditoriaActaModel
from app.models.cancha_model import CanchaModel
from app.models.colegio_model import ColegioModel
from app.models.equipo_model import EquipoModel
from app.models.evento_partido_model import EventoPartidoModel
from app.models.fase_model import FaseModel
from app.models.fila_posicion_model import FilaPosicionModel
from app.models.jugador_model import JugadorModel
from app.models.marcador_model import MarcadorModel
from app.models.pago_model import PagoModel
from app.models.partido_model import PartidoModel
from app.models.tabla_posiciones_model import TablaPosicionesModel
from app.models.torneo_model import TorneoModel
from app.models.usuario_model import (
    AdministradorModel,
    ArbitroModel,
    EntrenadorModel,
    UsuarioModel,
)

__all__ = [
    "AlineacionModel",
    "AuditoriaActaModel",
    "CanchaModel",
    "ColegioModel",
    "EquipoModel",
    "EventoPartidoModel",
    "FaseModel",
    "FilaPosicionModel",
    "JugadorModel",
    "MarcadorModel",
    "PagoModel",
    "PartidoModel",
    "TablaPosicionesModel",
    "TorneoModel",
    "UsuarioModel",
    "AdministradorModel",
    "EntrenadorModel",
    "ArbitroModel",
]
