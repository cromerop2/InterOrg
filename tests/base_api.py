"""Base común de las pruebas de API: BD SQLite en memoria, usuarios de prueba y sesión iniciada."""
import os
import sys
import unittest
from pathlib import Path

# Se configura antes de importar app para evitar usar la BD indicada en .env.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ.setdefault("SECRET_KEY", "clave-solo-para-pruebas-0123456789-abcdef")
os.environ.setdefault("BCRYPT_ROUNDS", "4")  # encriptar rápido en pruebas
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

    def habilitar_equipo(self, nombre="Los Halcones", desde=1, h=None, jugadores=2, **cambios):
        """Crea un equipo con `jugadores` jugadores, reporta su pago y lo habilita como Administrador."""
        equipo = self.crear_equipo(h, nombre, **cambios)
        self.agregar_jugadores(equipo["id"], jugadores, h, desde)
        pago = self.comprobante_ok(equipo["id"], h)
        r = self.client.patch(
            f"/equipos/{equipo['id']}/auditar", json={"id_pago": pago["id"]}, headers=self.h_admin
        )
        self.assertEqual(r.status_code, 200, r.text)
        return r.json()


class BasePartidoTest(BaseInscripcionTest):
    """Torneo En_Curso con 6 equipos Habilitados (A a F), 2 fases, 2 canchas y 2 árbitros.

    Equipos A, C y E son del entrenador 1; B, D y F del entrenador 2. Cada uno tiene 3 jugadores.
    Con INICIALIZAR_GRUPOS=True se arman "Grupo A" = [A, B, C] y "Grupo B" = [D, E]; F queda sin grupo.
    Reglas de prueba: 2 titulares y máximo 1 suplente por alineación. El torneo va del 2026-12-01 al 2026-12-20.
    """

    REGLAS = {**BaseInscripcionTest.REGLAS, "titulares": 2, "max_suplentes": 1}
    INICIALIZAR_GRUPOS = True

    def setUp(self):
        super().setUp()
        self.fase_grupos = self.crear_fase("Fase de Grupos", "Grupos")
        self.fase_final = self.crear_fase("Final", "Eliminatoria_Directa")

        duenos = {"A": self.h_ent1, "B": self.h_ent2, "C": self.h_ent1, "D": self.h_ent2, "E": self.h_ent1, "F": self.h_ent2}
        self.eq = {}
        for indice, (letra, h) in enumerate(duenos.items()):
            self.eq[letra] = self.habilitar_equipo(nombre=f"Equipo {letra}", desde=1 + indice * 10, h=h, jugadores=3)
        self.eq_pre = self.crear_equipo(self.h_ent2, nombre="Sin Pago")  # queda Preinscrito

        r = self.client.post(f"/torneos/{self.torneo['id']}/iniciar", headers=self.h_admin)
        self.assertEqual(r.status_code, 200, r.text)

        self.arb1_id = self.crear_usuario("Arbitro", "arb1@torneo.edu.co")
        self.arb2_id = self.crear_usuario("Arbitro", "arb2@torneo.edu.co")
        self.h_arb1 = self.cabecera("arb1@torneo.edu.co")
        self.h_arb2 = self.cabecera("arb2@torneo.edu.co")
        self.cancha1 = self.crear_cancha_api("Cancha 1")
        self.cancha2 = self.crear_cancha_api("Cancha 2")
        if self.INICIALIZAR_GRUPOS:
            self.crear_grupos()

    # ---------- datos base ----------
    def crear_fase(self, nombre, tipo):
        r = self.client.post(
            f"/torneos/{self.torneo['id']}/fases", json={"nombre": nombre, "tipo_formato": tipo}, headers=self.h_admin
        )
        self.assertEqual(r.status_code, 201, r.text)
        return r.json()

    def crear_cancha_api(self, nombre):
        datos = {"nombre": nombre, "direccion_sede": "Complejo Norte", "tipo_superficie": "Sintética"}
        r = self.client.post("/canchas/", json=datos, headers=self.h_admin)
        self.assertEqual(r.status_code, 201, r.text)
        return r.json()

    def crear_grupos(self):
        grupos = {"Grupo A": [self.eq[x]["id"] for x in "ABC"], "Grupo B": [self.eq[x]["id"] for x in "DE"]}
        r = self.client.post(f"/fases/{self.fase_grupos['id']}/grupos", json={"grupos": grupos}, headers=self.h_admin)
        self.assertEqual(r.status_code, 201, r.text)
        self.grupos = r.json()
        return self.grupos

    # ---------- partidos ----------
    def _id(self, equipo):
        """Acepta la letra del equipo ("A"), su diccionario o su id."""
        if isinstance(equipo, str):
            return self.eq[equipo]["id"]
        return equipo["id"] if isinstance(equipo, dict) else equipo

    def programar(self, local, visitante, hora="2026-12-05T10:00:00", cancha=None, fase=None, **extra):
        datos = {
            "fase_id": (fase or self.fase_grupos)["id"],
            "equipo_local_id": self._id(local),
            "equipo_visitante_id": self._id(visitante),
            "cancha_id": (cancha or self.cancha1)["id"],
            "fecha_hora": hora,
        }
        return self.client.post("/partidos/", json={**datos, **extra}, headers=self.h_admin)

    def programar_ok(self, local, visitante, **kwargs):
        r = self.programar(local, visitante, **kwargs)
        self.assertEqual(r.status_code, 201, r.text)
        return r.json()

    def ids_jugadores(self, letra):
        r = self.client.get(f"/equipos/{self.eq[letra]['id']}/jugadores", headers=self.h_admin)
        return [j["id"] for j in r.json()]
