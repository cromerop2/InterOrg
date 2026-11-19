"""Importa todos los modelos para que Base.metadata conozca cada tabla.

Al crear un modelo nuevo, agrégalo aquí; así create_all lo incluye.
"""

from app.models.colegio_model import ColegioModel
from app.models.usuario_model import (
    AdministradorModel,
    ArbitroModel,
    EntrenadorModel,
    UsuarioModel,
)

__all__ = [
    "ColegioModel",
    "UsuarioModel",
    "AdministradorModel",
    "EntrenadorModel",
    "ArbitroModel",
]
