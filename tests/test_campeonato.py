"""Pruebas de campeonato completo, autorización e integridad con SQLite temporal."""
import os
from pathlib import Path
import sys
import time
import unittest
import tempfile
from unittest.mock import patch

os.environ["DATABASE_URL"] = "sqlite://"
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database import Base, get_db
from app.main import app
from app.models.usuario_model import AdministradorModel, EntrenadorModel
from app.models.sesion_model import SesionModel
from app.models.fase_model import FaseModel
from app.models.grupo_model import GrupoModel
from app.models.partido_model import PartidoModel
from app.models.inscripcion_model import InscripcionModel
from app.core.enums import RolEnum
from app.core.security import hash_password
from app.services.campeonato_service import CampeonatoService
import test_colegio


class CampeonatoTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Reutiliza el hash solo en fixtures: cada prueba conserva su propia BD.
        cls.password_hash = hash_password("ClavePrueba123")

    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        @event.listens_for(self.engine, "connect")
        def activar_fk(conexion, _):
            conexion.execute("PRAGMA foreign_keys=ON")
        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)
        def temporal():
            with self.sessions() as db:
                yield db
        app.dependency_overrides[get_db] = temporal
        self.client = TestClient(app)
        with self.sessions() as db:
            comun = dict(nombre_completo="Prueba", telefono_contacto="3001234567", password_hash=self.password_hash)
            admin = AdministradorModel(**comun, email="admin@example.com", rol=RolEnum.ADMINISTRADOR)
            coach = EntrenadorModel(**comun, email="coach@example.com", rol=RolEnum.ENTRENADOR)
            db.add_all([admin, coach])
            db.commit()
            self.admin_id, self.coach_id = admin.id, coach.id
        self.token = self.login("admin@example.com")
        self.client.headers["Authorization"] = "Bearer " + self.token
        self.colegio = self.post("/colegios/", dict(nombre="Colegio", direccion="Calle 1",
                                representante_legal="Ana", telefono_contacto="3001234567"))
        self.torneo_datos = dict(nombre="Copa", categoria="Sub-17", fecha_inicio="2026-11-01",
                                fecha_fin="2026-12-31", numero_grupos=2, clasifican_por_grupo=2)
        self.torneo = self.post("/torneos/", self.torneo_datos)
        self.id = self.torneo["id"]
        self.equipos = []
        for n in range(6):
            equipo = self.post("/equipos/", dict(nombre=f"Equipo {n+1}", colegio_id=self.colegio["id"],
                                                 entrenador_id=self.coach_id))
            self.equipos.append(equipo)
            self.post(f"/torneos/{self.id}/equipos", {"equipo_id": equipo["id"]})

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.clear()
        self.engine.dispose()

    def login(self, email):
        return self.post("/auth/login", {"email": email, "password": "ClavePrueba123"}, 200)["access_token"]

    def post(self, ruta, datos=None, estado=201):
        r = self.client.post(ruta, json=datos)
        self.assertEqual(r.status_code, estado, r.text)
        return r.json()

    def get(self, ruta, estado=200):
        r = self.client.get(ruta)
        self.assertEqual(r.status_code, estado, r.text)
        return r.json()

    def resultado(self, partido, gl=1, gv=0, estado=200, **penales):
        r = self.client.put(f"/partidos/{partido['id']}/resultado",
                            json=dict(goles_local=gl, goles_visitante=gv, **penales))
        self.assertEqual(r.status_code, estado, r.text)
        return r.json()

    def fixture(self):
        return self.post(f"/torneos/{self.id}/fixture")

    def test_campeonato_completo_grupos_semifinal_y_final(self):
        grupos = self.fixture()
        self.assertEqual(len(grupos), 6)
        self.assertEqual({p["tipo_fase"] for p in grupos}, {"Grupos"})
        self.assertEqual(len(self.get(f"/torneos/{self.id}/posiciones")), 2)
        for partido in grupos:
            self.resultado(partido)
        tablas = self.get(f"/torneos/{self.id}/posiciones")
        self.assertTrue(all(sum(f["pj"] for f in g["posiciones"]) == 6 for g in tablas))
        semis = self.post(f"/torneos/{self.id}/avanzar")
        self.assertEqual(len(semis), 2)
        self.assertEqual(semis[0]["fase"], "Semifinal")
        self.post(f"/torneos/{self.id}/avanzar", estado=409)
        self.resultado(grupos[0], gl=9, estado=409)
        self.resultado(semis[0], gl=1, gv=1, penales_local=4, penales_visitante=5)
        self.resultado(semis[1])
        final = self.post(f"/torneos/{self.id}/avanzar")
        self.assertEqual(len(final), 1)
        self.assertEqual(final[0]["equipo_local_id"], semis[0]["equipo_visitante_id"])
        self.assertEqual(final[0]["equipo_visitante_id"], semis[1]["equipo_local_id"])
        self.resultado(final[0])
        seguimiento = self.get(f"/torneos/{self.id}/seguimiento")
        self.assertEqual(seguimiento["torneo"]["estado"], "Finalizado")
        self.assertEqual(seguimiento["campeon_id"], final[0]["equipo_local_id"])
        self.assertEqual(seguimiento["partidos_finalizados"], 9)
        self.assertEqual(seguimiento["porcentaje_fixture_completado"], 100)
        self.post(f"/torneos/{self.id}/avanzar", estado=409)
        # Una corrección administrativa de la final cambia al campeón sin duplicar partidos.
        self.resultado(final[0], gl=0, gv=2)
        self.assertEqual(self.get(f"/torneos/{self.id}/seguimiento")["campeon_id"], final[0]["equipo_visitante_id"])

    def test_solo_admin_puede_escribir_y_lecturas_son_publicas(self):
        fixture = self.fixture()
        self.client.headers.pop("Authorization")
        for ruta in ("/torneos/", "/equipos/", f"/torneos/{self.id}", f"/torneos/{self.id}/fixture",
                     f"/torneos/{self.id}/posiciones", f"/torneos/{self.id}/seguimiento",
                     f"/torneos/{self.id}/equipos"):
            self.get(ruta)
        rutas = [
            ("POST", "/torneos/", self.torneo_datos),
            ("POST", "/equipos/", dict(nombre="Intruso", colegio_id=self.colegio["id"], entrenador_id=self.coach_id)),
            ("POST", f"/torneos/{self.id}/equipos", {"equipo_id": self.equipos[0]["id"]}),
            ("POST", f"/torneos/{self.id}/fixture", None),
            ("POST", f"/torneos/{self.id}/avanzar", None),
            ("DELETE", f"/torneos/{self.id}/equipos/{self.equipos[0]['id']}", None),
            ("PUT", f"/partidos/{fixture[0]['id']}/resultado", {"goles_local": 1, "goles_visitante": 0}),
            ("PATCH", f"/partidos/{fixture[0]['id']}/programacion", {"fecha_hora": "2026-11-10T10:00:00-05:00", "sede": "Centro"}),
            ("POST", "/usuarios/", dict(nombre_completo="Intruso", email="intruso@example.com",
                                       telefono_contacto="123", rol="Administrador", password="ClavePrueba123")),
        ]
        for metodo, ruta, datos in rutas:
            with self.subTest(rol="visitante", ruta=ruta):
                self.assertEqual(self.client.request(metodo, ruta, json=datos).status_code, 401)
        coach_token = self.login("coach@example.com")
        self.client.headers["Authorization"] = "Bearer " + coach_token
        for metodo, ruta, datos in rutas:
            with self.subTest(rol="entrenador", ruta=ruta):
                self.assertEqual(self.client.request(metodo, ruta, json=datos).status_code, 403)

    def test_sesiones_invalidas_revocacion_caducidad_y_usuario_inactivo(self):
        self.assertNotIn("password_hash", self.get("/auth/me"))
        self.post("/auth/login", {"email": "admin@example.com", "password": "incorrecta"}, estado=401)
        self.client.headers["Authorization"] = "Bearer falso"
        self.get("/auth/me", estado=401)
        self.client.headers["Authorization"] = "Bearer " + self.token
        self.assertEqual(self.client.post("/auth/logout").status_code, 204)
        self.get("/auth/me", estado=401)
        self.token = self.login("admin@example.com")
        self.client.headers["Authorization"] = "Bearer " + self.token
        with self.sessions() as db:
            db.query(SesionModel).update({"expira_en": 0})
            db.commit()
        self.get("/auth/me", estado=401)
        self.token = self.login("admin@example.com")
        self.client.headers["Authorization"] = "Bearer " + self.token
        with self.sessions() as db:
            db.get(AdministradorModel, self.admin_id).estado_activo = False
            db.commit()
        self.get("/auth/me", estado=401)
        self.post("/auth/login", {"email": "admin@example.com", "password": "ClavePrueba123"}, estado=401)

    def test_crear_staff_hash_y_migrar_password_antigua(self):
        datos = dict(nombre_completo="Entrenador nuevo", email="nuevo@example.com",
                     telefono_contacto="3001234567", rol="Entrenador", password="ClavePrueba123")
        nuevo = self.post("/usuarios/", datos)
        self.assertNotIn("password", nuevo)
        with self.sessions() as db:
            usuario = db.get(EntrenadorModel, nuevo["id"])
            self.assertTrue(usuario.password_hash.startswith("$pbkdf2-sha256$"))
            usuario.password_hash = "ClavePrueba123"
            db.commit()
        self.login("nuevo@example.com")
        with self.sessions() as db:
            self.assertTrue(db.get(EntrenadorModel, nuevo["id"]).password_hash.startswith("$pbkdf2-sha256$"))
        self.post("/usuarios/", datos, estado=400)
        self.post("/usuarios/", {**datos, "email": "arbitro@example.com", "rol": "Arbitro"})
        self.post("/usuarios/", {**datos, "email": "admin2@example.com", "rol": "Administrador"})

    def test_jugadores_publicos_no_exponen_datos_personales(self):
        datos = dict(equipo_id=self.equipos[0]["id"], nombre_completo="Jugador",
                     identificacion="DOC1", fecha_nacimiento="2010-01-01", numero_camiseta=10)
        jugador = self.post("/jugadores/", datos)
        self.assertNotIn("identificacion", jugador)
        self.assertNotIn("fecha_nacimiento", jugador)
        self.post("/jugadores/", datos, estado=409)
        self.client.headers.pop("Authorization")
        self.assertEqual(self.get(f"/equipos/{self.equipos[0]['id']}/jugadores"), [jugador])
        self.post("/jugadores/", {**datos, "identificacion": "DOC2"}, estado=401)

    def test_recuperar_admin_revoca_sesiones_y_conserva_otras_cuentas(self):
        from app.reset_admin import restablecer_password
        coach_token = self.login("coach@example.com")
        with self.sessions() as db:
            with self.assertRaises(ValueError):
                restablecer_password(db, self.admin_id, "corta")
            with self.assertRaises(ValueError):
                restablecer_password(db, self.coach_id, "OtraClave123")
        self.get("/auth/me")  # Los intentos inválidos no revocaron la sesión.
        with self.sessions() as db:
            correo = restablecer_password(db, self.admin_id, "OtraClave123")
            self.assertEqual(correo, "admin@example.com")
        self.get("/auth/me", estado=401)
        self.post("/auth/login", {"email": correo, "password": "ClavePrueba123"}, estado=401)
        nuevo = self.post("/auth/login", {"email": correo, "password": "OtraClave123"}, estado=200)
        self.client.headers["Authorization"] = "Bearer " + nuevo["access_token"]
        self.assertEqual(self.get("/auth/me")["id"], self.admin_id)
        self.client.headers["Authorization"] = "Bearer " + coach_token
        self.assertEqual(self.get("/auth/me")["id"], self.coach_id)

    def test_equipos_reutilizables_y_retiro_de_inscripcion(self):
        otro = self.post("/torneos/", {**self.torneo_datos, "nombre": "Otra copa"})
        equipo = self.equipos[0]
        self.post(f"/torneos/{otro['id']}/equipos", {"equipo_id": equipo["id"]})
        self.post(f"/torneos/{otro['id']}/equipos", {"equipo_id": equipo["id"]}, estado=409)
        ruta = f"/torneos/{otro['id']}/equipos/{equipo['id']}"
        self.assertEqual(self.client.delete(ruta).status_code, 204)
        self.assertEqual(self.get(f"/torneos/{otro['id']}/equipos"), [])
        self.assertEqual(self.client.delete(ruta).status_code, 404)
        self.get(f"/equipos/{equipo['id']}")
        self.fixture()
        self.post(f"/torneos/{self.id}/equipos", {"equipo_id": equipo["id"]}, estado=409)
        self.assertEqual(self.client.delete(f"/torneos/{self.id}/equipos/{equipo['id']}").status_code, 409)

    def test_fixture_impar_no_repite_parejas_ni_equipos_en_jornada(self):
        partidos = self.fixture()
        self.assertEqual(len({tuple(sorted((p["equipo_local_id"], p["equipo_visitante_id"]))) for p in partidos}), 6)
        for grupo in {p["grupo_id"] for p in partidos}:
            for jornada in {p["jornada"] for p in partidos}:
                equipos = [e for p in partidos if p["grupo_id"] == grupo and p["jornada"] == jornada
                           for e in (p["equipo_local_id"], p["equipo_visitante_id"])]
                self.assertEqual(len(equipos), len(set(equipos)))
        self.post(f"/torneos/{self.id}/fixture", estado=409)
        self.assertEqual(len(self.get(f"/torneos/{self.id}/fixture")), 6)
        filtro = self.get(f"/torneos/{self.id}/fixture?equipo_id={self.equipos[0]['id']}")
        self.assertEqual(len(filtro), 2)
        self.assertEqual(self.get(f"/torneos/{self.id}/fixture?equipo_id=999"), [])

    def test_round_robin_entre_dos_y_diecisiete_equipos(self):
        for n in range(2, 18):
            cruces = CampeonatoService._round_robin(list(range(1, n + 1)))
            self.assertEqual(len(cruces), n * (n - 1) // 2)
            self.assertEqual(len({tuple(sorted((a, b))) for _, a, b in cruces}), len(cruces))
            for jornada in {j for j, _, _ in cruces}:
                jugadores = [e for j, a, b in cruces if j == jornada for e in (a, b)]
                self.assertEqual(len(jugadores), len(set(jugadores)))

    def test_resultado_corregido_no_duplica_puntos(self):
        partido = self.fixture()[0]
        self.resultado(partido, gl=2, gv=0)
        self.resultado(partido, gl=2, gv=0)
        tabla = next(g for g in self.get(f"/torneos/{self.id}/posiciones") if g["id"] == partido["grupo_id"])
        local = next(f for f in tabla["posiciones"] if f["equipo_id"] == partido["equipo_local_id"])
        self.assertEqual((local["pj"], local["puntos"], local["gf"]), (1, 3, 2))
        self.resultado(partido, gl=0, gv=1)
        tabla = next(g for g in self.get(f"/torneos/{self.id}/posiciones") if g["id"] == partido["grupo_id"])
        local = next(f for f in tabla["posiciones"] if f["equipo_id"] == partido["equipo_local_id"])
        self.assertEqual((local["pj"], local["puntos"], local["gf"], local["gc"]), (1, 0, 0, 1))

    def test_empates_y_penales(self):
        grupos = self.fixture()
        self.resultado(grupos[0], gl=-1, estado=422)
        self.resultado(grupos[0], gl=1, gv=1, penales_local=4, penales_visitante=3, estado=422)
        for partido in grupos:
            self.resultado(partido, gl=1, gv=1)
        tablas = self.get(f"/torneos/{self.id}/posiciones")
        self.assertTrue(all(f["puntos"] == 2 for g in tablas for f in g["posiciones"]))
        semis = self.post(f"/torneos/{self.id}/avanzar")
        self.resultado(semis[0], gl=1, gv=1, estado=422)
        self.resultado(semis[0], gl=1, gv=1, penales_local=4, penales_visitante=4, estado=422)
        self.resultado(semis[0], gl=2, gv=1, penales_local=4, penales_visitante=3, estado=422)
        self.resultado(semis[0], gl=1, gv=1, penales_local=4, estado=422)
        self.resultado(semis[0], gl=1, gv=1, penales_local=4, penales_visitante=3)

    def test_avanzar_requiere_todos_los_resultados_y_no_altera_otro_torneo(self):
        otro = self.post("/torneos/", {**self.torneo_datos, "nombre": "Otro"})
        self.post(f"/torneos/{self.id}/avanzar", estado=409)
        fixture = self.fixture()
        self.resultado(fixture[0])
        self.post(f"/torneos/{self.id}/avanzar", estado=409)
        self.assertEqual(self.get(f"/torneos/{otro['id']}/fixture"), [])
        self.assertEqual(self.get(f"/torneos/{otro['id']}/seguimiento")["torneo"]["estado"], "Inscripciones")

    def test_fixture_falla_sin_dejar_grupos_partidos_ni_cambiar_estado(self):
        with self.engine.begin() as db:
            db.execute(text("CREATE TRIGGER bloquear_fixture BEFORE INSERT ON partidos "
                            "BEGIN SELECT RAISE(ABORT, 'fallo de prueba'); END"))
        self.post(f"/torneos/{self.id}/fixture", estado=409)
        with self.sessions() as db:
            self.assertEqual(db.query(FaseModel).count(), 0)
            self.assertEqual(db.query(GrupoModel).count(), 0)
            self.assertEqual(db.query(PartidoModel).count(), 0)
            self.assertTrue(all(i.grupo_id is None for i in db.query(InscripcionModel)))
        self.assertEqual(self.get(f"/torneos/{self.id}")["estado"], "Inscripciones")
        with self.engine.begin() as db:
            db.execute(text("DROP TRIGGER bloquear_fixture"))
        self.fixture()

    def test_programacion_zona_horaria_fechas_y_conflictos(self):
        partidos = self.fixture()
        datos = dict(fecha_hora="2026-11-15T10:00:00-05:00", sede="Cancha Central")
        ruta = f"/partidos/{partidos[0]['id']}/programacion"
        respuesta = self.client.patch(ruta, json=datos)
        self.assertEqual(respuesta.status_code, 200, respuesta.text)
        self.assertEqual(respuesta.json()["fecha_hora"], "2026-11-15T15:00:00Z")
        self.assertEqual(self.client.patch(ruta, json={**datos, "fecha_hora": "2026-11-15T10:00:00"}).status_code, 422)
        self.assertEqual(self.client.patch(ruta, json={**datos, "fecha_hora": "2027-01-01T10:00:00Z"}).status_code, 422)
        self.assertEqual(self.client.patch(f"/partidos/{partidos[1]['id']}/programacion", json=datos).status_code, 409)
        self.resultado(partidos[0])
        self.assertEqual(self.client.patch(ruta, json=datos).status_code, 409)

    def test_validacion_campeonato_equipos_y_registros_inexistentes(self):
        for cambios in ({"numero_grupos": 3}, {"clasifican_por_grupo": 0},
                        {"fecha_fin": "2020-01-01"}, {"nombre": "  "}, {"extra": True}):
            self.post("/torneos/", {**self.torneo_datos, **cambios}, estado=422)
        insuficiente = self.post("/torneos/", {**self.torneo_datos, "nombre": "Sin equipos"})
        self.post(f"/torneos/{insuficiente['id']}/fixture", estado=409)
        self.assertEqual(self.get(f"/torneos/{insuficiente['id']}/posiciones"), [])
        for ruta in ("/torneos/999", "/torneos/999/fixture", "/torneos/999/posiciones",
                     "/torneos/999/seguimiento", "/equipos/999", "/equipos/999/jugadores"):
            self.get(ruta, estado=404)
        self.post(f"/torneos/{self.id}/equipos", {"equipo_id": 999}, estado=404)
        self.post("/equipos/", dict(nombre="Equipo", colegio_id=self.colegio["id"], entrenador_id=self.admin_id), estado=404)
        self.post("/equipos/", dict(nombre="Equipo", colegio_id=999, entrenador_id=self.coach_id), estado=404)


class CampeonatoServidorTest(unittest.TestCase):
    """Ejecución por HTTP real y persistencia después de reiniciar Uvicorn."""
    servidor = test_colegio.ColegioServidorTest.servidor

    def test_flujo_http_y_consulta_publica_tras_reinicio(self):
        with tempfile.TemporaryDirectory(prefix="campeonato-test-") as temporal:
            carpeta = Path(temporal)
            with self.servidor(carpeta) as cliente:
                def crear(ruta, datos=None):
                    respuesta = cliente.post(ruta, json=datos)
                    self.assertEqual(respuesta.status_code, 201, respuesta.text)
                    return respuesta.json()
                coach = crear("/usuarios/", dict(nombre_completo="Coach", email="coach@example.com",
                              telefono_contacto="3001234567", rol="Entrenador", password="ClavePrueba123"))
                colegio = crear("/colegios/", dict(nombre="Colegio HTTP", direccion="Calle 1",
                                representante_legal="Ana", telefono_contacto="3001234567"))
                torneo = crear("/torneos/", dict(nombre="Copa HTTP", categoria="Sub-17",
                               fecha_inicio="2026-11-01", fecha_fin="2026-12-31",
                               numero_grupos=2, clasifican_por_grupo=1))
                for n in range(4):
                    equipo = crear("/equipos/", dict(nombre=f"Equipo {n}", colegio_id=colegio["id"],
                                                     entrenador_id=coach["id"]))
                    crear(f"/torneos/{torneo['id']}/equipos", {"equipo_id": equipo["id"]})
                grupos = crear(f"/torneos/{torneo['id']}/fixture")
                self.assertEqual(len(grupos), 2)
                for partido in grupos:
                    respuesta = cliente.put(f"/partidos/{partido['id']}/resultado",
                                            json={"goles_local": 2, "goles_visitante": 1})
                    self.assertEqual(respuesta.status_code, 200, respuesta.text)
                final = crear(f"/torneos/{torneo['id']}/avanzar")[0]
                respuesta = cliente.put(f"/partidos/{final['id']}/resultado",
                                        json={"goles_local": 0, "goles_visitante": 1})
                self.assertEqual(respuesta.status_code, 200, respuesta.text)
                esperado = cliente.get(f"/torneos/{torneo['id']}/seguimiento").json()
                self.assertEqual(esperado["campeon_id"], final["equipo_visitante_id"])
            with self.servidor(carpeta) as cliente:
                cliente.headers.pop("Authorization")
                respuesta = cliente.get(f"/torneos/{torneo['id']}/seguimiento")
                self.assertEqual(respuesta.status_code, 200, respuesta.text)
                self.assertEqual(respuesta.json(), esperado)
                self.assertEqual(len(cliente.get(f"/torneos/{torneo['id']}/fixture").json()), 3)
                self.assertEqual(len(cliente.get(f"/torneos/{torneo['id']}/posiciones").json()), 2)


if __name__ == "__main__":
    unittest.main()
