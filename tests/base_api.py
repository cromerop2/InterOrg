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


class BaseInscripcionTest(BaseApiTest):
    """Agrega un colegio, un torneo Sub-17 con reglas pequeñas y dos entrenadores con sesión iniciada.

    Reglas del torneo de prueba: mínimo 2 jugadores, máximo 3, un solo equipo Habilitado para iniciar.
    """

    REGLAS = {"min_jugadores": 2, "max_jugadores": 3, "min_equipos": 1}

    def setUp(self):
        super().setUp()
        self._contador_referencias = 0
        self.colegio = self.crear_colegio_api()
        self.torneo = self.crear_torneo_api()
        self.ent1_id = self.crear_usuario("Entrenador", "ent1@torneo.edu.co")
        self.ent2_id = self.crear_usuario("Entrenador", "ent2@torneo.edu.co")
        self.h_ent1 = self.cabecera("ent1@torneo.edu.co")
        self.h_ent2 = self.cabecera("ent2@torneo.edu.co")

    # ---------- datos base ----------
    def crear_colegio_api(self, nombre="Colegio Central", **cambios):
        datos = {
            "nombre": nombre,
            "direccion": "Calle 1",
            "representante_legal": "Rector",
            "telefono_contacto": "3001234567",
        }
        r = self.client.post("/colegios/", json={**datos, **cambios}, headers=self.h_admin)
        self.assertEqual(r.status_code, 201, r.text)
        return r.json()

    def crear_torneo_api(self, **cambios):
        datos = {
            "nombre": "Copa Intercolegial 2026",
            "categoria": "Sub-17",
            "fecha_inicio": "2026-12-01",
            "fecha_fin": "2026-12-20",
            "reglas": dict(self.REGLAS),
        }
        r = self.client.post("/torneos/", json={**datos, **cambios}, headers=self.h_admin)
        self.assertEqual(r.status_code, 201, r.text)
        return r.json()

    # ---------- equipos, jugadores y pagos ----------
    def crear_equipo(self, h=None, nombre="Los Halcones", **cambios):
        datos = {"colegio_id": self.colegio["id"], "torneo_id": self.torneo["id"], "nombre": nombre}
        r = self.client.post("/equipos/", json={**datos, **cambios}, headers=h or self.h_ent1)
        self.assertEqual(r.status_code, 201, r.text)
        return r.json()

    @staticmethod
    def datos_jugador(numero, **cambios):
        datos = {
            "nombre_completo": f"Jugador {numero}",
            "identificacion": f"1000{numero:03d}",
            "fecha_nacimiento": "2010-05-10",
        }
        datos.update(cambios)
        return datos

    def agregar_jugadores(self, id_equipo, cantidad, h=None, desde=1):
        for numero in range(desde, desde + cantidad):
            r = self.client.post(
                f"/equipos/{id_equipo}/jugadores", json=self.datos_jugador(numero), headers=h or self.h_ent1
            )
            self.assertEqual(r.status_code, 201, r.text)

    def comprobante(self, id_equipo, h=None, **cambios):
        """Envía un pago con referencia única y devuelve la respuesta sin comprobarla."""
        self._contador_referencias += 1
        datos = {
            "monto": "150000.00",
            "metodo_pago": "Transferencia",
            "referencia_transaccion": f"REF-{self._contador_referencias}",
        }
        return self.client.post(f"/equipos/{id_equipo}/pagos", json={**datos, **cambios}, headers=h or self.h_ent1)

    def comprobante_ok(self, id_equipo, h=None, **cambios):
        r = self.comprobante(id_equipo, h, **cambios)
        self.assertEqual(r.status_code, 201, r.text)
        return r.json()

    def habilitar_equipo(self, nombre="Los Halcones", desde=1, h=None, **cambios):
        """Crea un equipo con 2 jugadores, reporta su pago y lo habilita como Administrador."""
        equipo = self.crear_equipo(h, nombre, **cambios)
        self.agregar_jugadores(equipo["id"], 2, h, desde)
        pago = self.comprobante_ok(equipo["id"], h)
        r = self.client.patch(
            f"/equipos/{equipo['id']}/auditar", json={"id_pago": pago["id"]}, headers=self.h_admin
        )
        self.assertEqual(r.status_code, 200, r.text)
        return r.json()
