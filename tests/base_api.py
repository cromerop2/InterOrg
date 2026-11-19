"""Base común de las pruebas de API: BD SQLite en memoria, usuarios de prueba y sesión iniciada."""
import os
import sys
import unittest
from pathlib import Path

# Se configura antes de importar app para evitar usar la BD indicada en .env.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ.setdefault("SECRET_KEY", "clave-solo-para-pruebas-0123456789-abcdef")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app import models  # noqa: F401  (registra todas las tablas)
from app.repositories.colegio_repository import ColegioRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.usuario_schema import AdministradorCreate, ArbitroCreate, EntrenadorCreate
from app.services.usuario_service import UsuarioService

CLAVE = "Clave-segura-123"
_ESQUEMA_POR_ROL = {
    "Administrador": AdministradorCreate,
    "Entrenador": EntrenadorCreate,
    "Arbitro": ArbitroCreate,
}


class BaseApiTest(unittest.TestCase):
    """Cada prueba tiene una BD vacía, un administrador sembrado y su token en self.h_admin."""

    def setUp(self):
        self.engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
        Base.metadata.create_all(self.engine)
        self.Sesion = sessionmaker(bind=self.engine, autoflush=False)

        def db_temporal():
            db = self.Sesion()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = db_temporal
        self.client = TestClient(app)
        self.crear_usuario("Administrador", "admin@torneo.edu.co")
        self.h_admin = self.cabecera("admin@torneo.edu.co")

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.clear()
        self.engine.dispose()

    def crear_usuario(self, rol, email, **extra):
        """Crea un usuario directo en la BD (sin pasar por la API) y devuelve su id."""
        with self.Sesion() as db:
            servicio = UsuarioService(UsuarioRepository(db), ColegioRepository(db))
            datos = _ESQUEMA_POR_ROL[rol](
                rol=rol,
                nombre_completo="Persona Prueba",
                email=email,
                telefono_contacto="3000000000",
                password=CLAVE,
                **extra,
            )
            return servicio.registrar_usuario(datos).id

    def cabecera(self, email):
        """Inicia sesión y devuelve la cabecera Authorization lista para usar."""
        r = self.client.post("/auth/login", json={"email": email, "password": CLAVE})
        self.assertEqual(r.status_code, 200, r.text)
        return {"Authorization": f"Bearer {r.json()['access_token']}"}
