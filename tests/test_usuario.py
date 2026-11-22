"""Pruebas de seguridad y usuarios con SQLite en memoria, sin usar la BD de .env."""
import os
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Se configura antes de importar app para evitar usar la BD indicada en .env.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ.setdefault("SECRET_KEY", "clave-solo-para-pruebas-0123456789-abcdef")
os.environ.setdefault("BCRYPT_ROUNDS", "4")  # encriptar rápido en pruebas
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

import jwt
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.core.security import hashear_password, verificar_password
from app.database import Base, get_db
from app.main import app
from app.models import UsuarioModel  # importar app.models registra todas las tablas
from app.repositories.colegio_repository import ColegioRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.colegio_schema import ColegioCreate
from app.schemas.usuario_schema import AdministradorCreate, EntrenadorCreate
from app.services.usuario_service import UsuarioService

CLAVE = "Clave-segura-123"


class SeguridadTest(unittest.TestCase):
    def test_hash_no_es_la_contrasena_y_se_verifica(self):
        hash_ = hashear_password(CLAVE)
        self.assertNotEqual(hash_, CLAVE)
        self.assertTrue(verificar_password(CLAVE, hash_))
        self.assertFalse(verificar_password("otra-clave", hash_))

    def test_dos_hashes_de_la_misma_clave_son_distintos(self):
        self.assertNotEqual(hashear_password(CLAVE), hashear_password(CLAVE))

    def test_contrasena_demasiado_larga(self):
        with self.assertRaises(ValueError):
            hashear_password("a" * 73)
        self.assertFalse(verificar_password("a" * 73, hashear_password(CLAVE)))

    def test_valor_guardado_en_texto_plano_no_valida(self):
        # Usuarios viejos con la contraseña sin hash no deben provocar un error 500.
        self.assertFalse(verificar_password(CLAVE, CLAVE))


class UsuarioApiTest(unittest.TestCase):
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

        self.admin = self.sembrar_admin("admin@torneo.edu.co")
        self.token_admin = self.login("admin@torneo.edu.co")

    def tearDown(self):
        app.dependency_overrides.clear()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    # ---------- utilidades ----------
    def servicio(self, db):
        return UsuarioService(UsuarioRepository(db), ColegioRepository(db))

    def sembrar_admin(self, email):
        """Crea el primer administrador directo en la BD (como hace scripts/crear_admin.py)."""
        with self.Sesion() as db:
            return self.servicio(db).registrar_usuario(
                AdministradorCreate(
                    rol="Administrador",
                    nombre_completo="Admin Uno",
                    email=email,
                    telefono_contacto="3000000000",
                    password=CLAVE,
                )
            ).id

    def crear_colegio(self, activo=True):
        with self.Sesion() as db:
            return ColegioRepository(db).crear_colegio(
                ColegioCreate(
                    nombre="Colegio Central",
                    direccion="Calle 1",
                    representante_legal="Rector",
                    telefono_contacto="3001234567",
                    estado_activo=activo,
                )
            ).id

    def login(self, email, password=CLAVE):
        respuesta = self.client.post("/auth/login", json={"email": email, "password": password})
        self.assertEqual(respuesta.status_code, 200, respuesta.text)
        return respuesta.json()["access_token"]

    def cab(self, token):
        return {"Authorization": f"Bearer {token}"}

    def datos(self, rol, email, **extra):
        base = {
            "rol": rol,
            "nombre_completo": "Persona Prueba",
            "email": email,
            "telefono_contacto": "3111111111",
            "password": CLAVE,
        }
        base.update(extra)
        return base

    def crear_como_admin(self, payload):
        return self.client.post("/usuarios/", json=payload, headers=self.cab(self.token_admin))

    # ---------- login ----------
    def test_login_correcto_devuelve_token_y_rol(self):
        r = self.client.post("/auth/login", json={"email": "admin@torneo.edu.co", "password": CLAVE})
        self.assertEqual(r.status_code, 200)
        cuerpo = r.json()
        self.assertEqual(cuerpo["rol"], "Administrador")
        self.assertEqual(cuerpo["token_type"], "bearer")
        payload = jwt.decode(cuerpo["access_token"], settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        self.assertEqual(payload["sub"], str(self.admin))

    def test_login_no_distingue_correo_inexistente_de_clave_mala(self):
        malo = self.client.post("/auth/login", json={"email": "admin@torneo.edu.co", "password": "incorrecta"})
        inexistente = self.client.post("/auth/login", json={"email": "nadie@torneo.edu.co", "password": CLAVE})
        self.assertEqual(malo.status_code, 401)
        self.assertEqual(inexistente.status_code, 401)
        self.assertEqual(malo.json(), inexistente.json())

    def test_login_ignora_mayusculas_del_correo(self):
        self.login("ADMIN@Torneo.edu.co")

    def test_cuenta_suspendida_no_puede_iniciar_sesion(self):
        creado = self.crear_como_admin(self.datos("Arbitro", "arb@torneo.edu.co")).json()
        self.client.patch(
            f"/usuarios/{creado['id']}/estado", json={"estado_activo": False}, headers=self.cab(self.token_admin)
        )
        r = self.client.post("/auth/login", json={"email": "arb@torneo.edu.co", "password": CLAVE})
        self.assertEqual(r.status_code, 401)

    def test_contrasena_se_guarda_hasheada(self):
        self.crear_como_admin(self.datos("Arbitro", "arb@torneo.edu.co"))
        with self.Sesion() as db:
            usuario = db.query(UsuarioModel).filter_by(email="arb@torneo.edu.co").one()
            self.assertNotEqual(usuario.password_hash, CLAVE)
            self.assertTrue(verificar_password(CLAVE, usuario.password_hash))

    # ---------- tokens ----------
    def test_sin_token_o_token_invalido_es_401(self):
        self.assertEqual(self.client.get("/auth/me").status_code, 401)
        self.assertEqual(self.client.get("/auth/me", headers=self.cab("no-es-un-jwt")).status_code, 401)

    def test_token_con_firma_falsa_es_401(self):
        falso = jwt.encode(
            {"sub": str(self.admin), "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
            "otra-clave-distinta-de-32-caracteres-o-mas",
            algorithm=settings.ALGORITHM,
        )
        self.assertEqual(self.client.get("/auth/me", headers=self.cab(falso)).status_code, 401)

    def test_token_vencido_es_401(self):
        vencido = jwt.encode(
            {"sub": str(self.admin), "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )
        self.assertEqual(self.client.get("/auth/me", headers=self.cab(vencido)).status_code, 401)

    def test_me_devuelve_el_perfil_sin_hash(self):
        r = self.client.get("/auth/me", headers=self.cab(self.token_admin))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["email"], "admin@torneo.edu.co")
        self.assertEqual(r.json()["nivel_acceso"], "Total")
        self.assertNotIn("password_hash", r.json())
        self.assertNotIn("password", r.json())

    # ---------- permisos ----------
    def test_crear_usuario_exige_ser_administrador(self):
        payload = self.datos("Arbitro", "arb@torneo.edu.co")
        self.assertEqual(self.client.post("/usuarios/", json=payload).status_code, 401)

        self.crear_como_admin(self.datos("Entrenador", "ent@torneo.edu.co"))
        token_entrenador = self.login("ent@torneo.edu.co")
        r = self.client.post("/usuarios/", json=payload, headers=self.cab(token_entrenador))
        self.assertEqual(r.status_code, 403)

    def test_listar_solo_administrador(self):
        self.crear_como_admin(self.datos("Entrenador", "ent@torneo.edu.co"))
        token_entrenador = self.login("ent@torneo.edu.co")
        self.assertEqual(self.client.get("/usuarios/", headers=self.cab(token_entrenador)).status_code, 403)
        r = self.client.get("/usuarios/", headers=self.cab(self.token_admin))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()), 2)

    def test_un_usuario_solo_ve_su_propia_cuenta(self):
        ent = self.crear_como_admin(self.datos("Entrenador", "ent@torneo.edu.co")).json()
        token = self.login("ent@torneo.edu.co")
        self.assertEqual(self.client.get(f"/usuarios/{ent['id']}", headers=self.cab(token)).status_code, 200)
        self.assertEqual(self.client.get(f"/usuarios/{self.admin}", headers=self.cab(token)).status_code, 403)
        self.assertEqual(self.client.get("/usuarios/999", headers=self.cab(self.token_admin)).status_code, 404)

    # ---------- registro por rol ----------
    def test_crear_entrenador_con_colegio(self):
        colegio_id = self.crear_colegio()
        r = self.crear_como_admin(self.datos("Entrenador", "ent@torneo.edu.co", colegio_id=colegio_id))
        self.assertEqual(r.status_code, 201, r.text)
        self.assertEqual(r.json()["rol"], "Entrenador")
        self.assertEqual(r.json()["colegio_id"], colegio_id)
        self.assertNotIn("password_hash", r.json())

    def test_entrenador_con_colegio_inexistente_o_inactivo(self):
        r = self.crear_como_admin(self.datos("Entrenador", "a@torneo.edu.co", colegio_id=999))
        self.assertEqual(r.status_code, 404)
        inactivo = self.crear_colegio(activo=False)
        r = self.crear_como_admin(self.datos("Entrenador", "b@torneo.edu.co", colegio_id=inactivo))
        self.assertEqual(r.status_code, 400)

    def test_varios_arbitros_sin_numero_colegiado(self):
        # Regresión: antes se guardaba "PENDIENTE" y el segundo árbitro chocaba con unique.
        for correo in ("a1@torneo.edu.co", "a2@torneo.edu.co"):
            r = self.crear_como_admin(self.datos("Arbitro", correo))
            self.assertEqual(r.status_code, 201, r.text)
            self.assertIsNone(r.json()["numero_colegiado"])

    def test_numero_colegiado_duplicado(self):
        self.assertEqual(
            self.crear_como_admin(self.datos("Arbitro", "a1@torneo.edu.co", numero_colegiado="C-1")).status_code, 201
        )
        r = self.crear_como_admin(self.datos("Arbitro", "a2@torneo.edu.co", numero_colegiado="C-1"))
        self.assertEqual(r.status_code, 409)

    def test_correo_duplicado_ignora_mayusculas(self):
        self.crear_como_admin(self.datos("Arbitro", "dup@torneo.edu.co"))
        r = self.crear_como_admin(self.datos("Entrenador", "DUP@torneo.edu.co"))
        self.assertEqual(r.status_code, 409)

    def test_campos_que_no_corresponden_al_rol_dan_422(self):
        r = self.crear_como_admin(self.datos("Administrador", "x@torneo.edu.co", colegio_id=1))
        self.assertEqual(r.status_code, 422)

    def test_rol_invalido_y_clave_corta_dan_422(self):
        self.assertEqual(self.crear_como_admin(self.datos("Espectador", "y@torneo.edu.co")).status_code, 422)
        self.assertEqual(
            self.crear_como_admin(self.datos("Arbitro", "z@torneo.edu.co", password="corta")).status_code, 422
        )

    def test_clave_de_mas_de_72_bytes_se_rechaza_sin_error_500(self):
        # 40 caracteres de 2 bytes = 80 bytes: pasa max_length=72 caracteres pero no el límite de bcrypt.
        r = self.crear_como_admin(self.datos("Arbitro", "w@torneo.edu.co", password="ñ" * 40))
        self.assertEqual(r.status_code, 422)

    # ---------- suspensión ----------
    def test_suspender_invalida_el_token_existente_y_se_puede_reactivar(self):
        ent = self.crear_como_admin(self.datos("Entrenador", "ent@torneo.edu.co")).json()
        token = self.login("ent@torneo.edu.co")
        self.assertEqual(self.client.get("/auth/me", headers=self.cab(token)).status_code, 200)

        r = self.client.patch(
            f"/usuarios/{ent['id']}/estado", json={"estado_activo": False}, headers=self.cab(self.token_admin)
        )
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.json()["estado_activo"])
        self.assertEqual(self.client.get("/auth/me", headers=self.cab(token)).status_code, 401)

        self.client.patch(
            f"/usuarios/{ent['id']}/estado", json={"estado_activo": True}, headers=self.cab(self.token_admin)
        )
        self.assertEqual(self.client.get("/auth/me", headers=self.cab(token)).status_code, 200)

    def test_administrador_no_puede_suspenderse_a_si_mismo(self):
        r = self.client.patch(
            f"/usuarios/{self.admin}/estado", json={"estado_activo": False}, headers=self.cab(self.token_admin)
        )
        self.assertEqual(r.status_code, 400)

    def test_cambiar_estado_de_usuario_inexistente(self):
        r = self.client.patch(
            "/usuarios/999/estado", json={"estado_activo": False}, headers=self.cab(self.token_admin)
        )
        self.assertEqual(r.status_code, 404)


if __name__ == "__main__":
    unittest.main()
