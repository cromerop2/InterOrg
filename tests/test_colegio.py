"""Pruebas con SQLite temporal en memoria/disco, sin usar la BD de .env."""
import os
from contextlib import contextmanager
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import unittest

# Se configura antes de importar app para evitar usar la BD indicada en .env.
os.environ["DATABASE_URL"] = "sqlite://"
# Permite importar el paquete app desde este archivo ubicado en tests.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from fastapi.testclient import TestClient
import httpx
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import get_db
from app.main import app
from app.models.colegio_model import ColegioModel
from app.repositories.colegio_repository import ColegioRepository
from app.schemas.colegio_schema import ColegioCreate, ColegioUpdate


class ColegioAPITest(unittest.TestCase):
    """Prueba las capas de Colegio juntas con una BD nueva para cada caso."""

    def setUp(self):
        """Prepara una tabla vacía, el cliente HTTP y los datos de ejemplo."""
        # StaticPool comparte la misma BD en memoria con el hilo de TestClient.
        # check_same_thread=False permite usar la conexión desde ese hilo.
        self.engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
        ColegioModel.__table__.create(self.engine)
        self.sessions = sessionmaker(bind=self.engine)

        def db_temporal():
            """Entrega y cierra una sesión de prueba para cada petición."""
            with self.sessions() as db:
                yield db

        # Sustituye solo la conexión: router, servicio y repositorio son reales.
        app.dependency_overrides[get_db] = db_temporal
        # TestClient envía peticiones a la app sin abrir un puerto de red.
        self.client = TestClient(app)
        self.datos = {
            "nombre": "Colegio San José",
            "direccion": "Calle 10 # 20-30",
            "representante_legal": "Ana Pérez",
            "telefono_contacto": "3001234567",
        }

    def tearDown(self):
        """Cierra recursos y restaura las dependencias al terminar cada prueba."""
        self.client.close()
        app.dependency_overrides.clear()
        self.engine.dispose()

    def crear(self, **cambios):
        """Crea un colegio de ejemplo, con los cambios que necesite cada caso."""
        respuesta = self.client.post("/colegios/", json={**self.datos, **cambios})
        self.assertEqual(respuesta.status_code, 201, respuesta.text)
        return respuesta.json()

    def test_crear_y_consultar_colegio(self):
        """Comprueba ID generado, valores por defecto y consulta del registro."""
        colegio = self.crear()
        self.assertIsInstance(colegio["id"], int)
        self.assertTrue(colegio["estado_activo"])
        self.assertIsNone(colegio["email_institucional"])
        respuesta = self.client.get(f"/colegios/{colegio['id']}")
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json(), colegio)

    def test_nombre_duplicado_incluso_si_esta_inactivo(self):
        """Verifica que desactivar un colegio no libere su nombre para otro."""
        self.crear(estado_activo=False)
        respuesta = self.client.post("/colegios/", json=self.datos)
        self.assertEqual(respuesta.status_code, 409)
        self.assertEqual(len(self.client.get("/colegios/?activos_solamente=false").json()), 1)

    def test_listar_solo_activos_por_defecto(self):
        """Comprueba la lista vacía y el filtro opcional de colegios activos."""
        self.assertEqual(self.client.get("/colegios/").json(), [])
        activo = self.crear()
        inactivo = self.crear(nombre="Colegio Inactivo", estado_activo=False)
        self.assertEqual(self.client.get("/colegios/").json(), [activo])
        self.assertEqual(
            self.client.get("/colegios/?activos_solamente=false").json(), [activo, inactivo]
        )

    def test_actualizar_contacto_desactivar_y_reactivar(self):
        """Actualiza contacto y estado, conservando los campos que se omiten."""
        colegio = self.crear(email_institucional="info@colegio.edu.co")
        ruta = f"/colegios/{colegio['id']}"
        cambios = {
            "direccion": "Carrera 8 # 12-40",
            "representante_legal": "Luis Gómez",
            "telefono_contacto": "6011234567",
            "estado_activo": False,
        }
        respuesta = self.client.patch(ruta, json=cambios)
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json(), {**colegio, **cambios})
        self.assertEqual(self.client.get("/colegios/").json(), [])
        self.assertEqual(self.client.get(ruta).json(), respuesta.json())
        respuesta = self.client.patch(ruta, json={"estado_activo": True})
        self.assertTrue(respuesta.json()["estado_activo"])
        self.assertEqual(len(self.client.get("/colegios/").json()), 1)

    def test_correo_opcional_se_puede_borrar(self):
        """Comprueba que enviar null elimine el correo previamente guardado."""
        colegio = self.crear(email_institucional="info@colegio.edu.co")
        respuesta = self.client.patch(
            f"/colegios/{colegio['id']}", json={"email_institucional": None}
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertIsNone(respuesta.json()["email_institucional"])

    def test_actualizar_nombre_y_rechazar_conflictos_sin_cambiar_otros_campos(self):
        """Rechaza nombres ocupados sin guardar el resto de una petición inválida."""
        primero = self.crear()
        segundo = self.crear(nombre="Colegio Dos")
        ruta = f"/colegios/{segundo['id']}"
        respuesta = self.client.patch(
            ruta, json={"nombre": primero["nombre"], "direccion": "Otra dirección"}
        )
        self.assertEqual(respuesta.status_code, 409)
        self.assertEqual(self.client.get(ruta).json(), segundo)
        self.assertEqual(self.client.patch(ruta, json={"nombre": segundo["nombre"]}).status_code, 200)
        respuesta = self.client.patch(ruta, json={"nombre": "Colegio Renombrado"})
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(self.client.get(ruta).json()["nombre"], "Colegio Renombrado")

    def test_colegio_inexistente(self):
        """Exige 404 al consultar o actualizar un ID que no está registrado."""
        self.assertEqual(self.client.get("/colegios/999").status_code, 404)
        self.assertEqual(self.client.patch("/colegios/999", json={"estado_activo": False}).status_code, 404)

    def test_validaciones_de_entrada(self):
        """Exige 422 para datos inválidos en creación y actualización."""
        colegio = self.crear()
        ruta = f"/colegios/{colegio['id']}"
        for campo in self.datos:
            for valor in (None, "", "   "):
                # subTest identifica el campo y valor concretos si un caso falla.
                with self.subTest(campo=campo, valor=valor):
                    self.assertEqual(
                        self.client.post("/colegios/", json={**self.datos, campo: valor}).status_code, 422
                    )
                    self.assertEqual(self.client.patch(ruta, json={campo: valor}).status_code, 422)
            with self.subTest(omitido=campo):
                datos = {clave: valor for clave, valor in self.datos.items() if clave != campo}
                self.assertEqual(self.client.post("/colegios/", json=datos).status_code, 422)
        for cambios in ({"email_institucional": "incorrecto"}, {"estado_activo": None}, {"desconocido": 1}):
            with self.subTest(cambios=cambios):
                self.assertEqual(self.client.post("/colegios/", json={**self.datos, **cambios}).status_code, 422)
                self.assertEqual(self.client.patch(ruta, json=cambios).status_code, 422)
        for identificador in (0, -1, "abc"):
            with self.subTest(identificador=identificador):
                self.assertEqual(self.client.get(f"/colegios/{identificador}").status_code, 422)

    def test_espacios_y_actualizacion_vacia(self):
        """Verifica la limpieza de espacios y que un PATCH vacío conserve los datos."""
        colegio = self.crear(nombre="  Colegio Nuevo  ")
        self.assertEqual(colegio["nombre"], "Colegio Nuevo")
        respuesta = self.client.patch(f"/colegios/{colegio['id']}", json={})
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json(), colegio)
        respuesta = self.client.post("/colegios/", json={**self.datos, "nombre": "Colegio Nuevo"})
        self.assertEqual(respuesta.status_code, 409)

    def test_bd_impide_duplicados_y_recupera_la_sesion(self):
        """Prueba la restricción de la BD directamente, sin validación del servicio."""
        with self.sessions() as db:
            repo = ColegioRepository(db)
            primero = repo.crear_colegio(ColegioCreate(**self.datos))
            with self.assertRaises(IntegrityError):
                repo.crear_colegio(ColegioCreate(**self.datos))
            segundo = repo.crear_colegio(ColegioCreate(**{**self.datos, "nombre": "Colegio Dos"}))
            with self.assertRaises(IntegrityError):
                repo.actualizar_detalles(segundo.id, ColegioUpdate(nombre=primero.nombre))
            self.assertEqual(repo.obtener_por_id(segundo.id).nombre, "Colegio Dos")
            self.assertEqual(len(repo.obtener_todos()), 2)
            self.assertIsNone(repo.actualizar_detalles(999, ColegioUpdate(nombre="Ausente")))


class ColegioServidorTest(unittest.TestCase):
    """Comprueba peticiones por red y persistencia con un proceso Uvicorn real."""

    @contextmanager
    def servidor(self, carpeta):
        """Arranca la app real con su get_db y una BD temporal persistente."""
        # El puerto 0 pide al sistema un puerto libre para esta ejecución.
        with socket.socket() as socket_libre:
            socket_libre.bind(("127.0.0.1", 0))
            puerto = socket_libre.getsockname()[1]
        entorno = os.environ.copy()
        # El proceso hijo usa su propio archivo SQLite, nunca la BD del .env.
        entorno["DATABASE_URL"] = "sqlite:///" + (carpeta / "colegios.sqlite3").as_posix()
        # Este archivo sirve como señal para cerrar Uvicorn de forma ordenada.
        detener = carpeta / f"detener-{puerto}"
        # Código ejecutado en otro proceso: prepara la tabla, sirve la app y
        # vigila la señal de cierre en un hilo para liberar la BD al terminar.
        codigo = f"""
from pathlib import Path
import threading
import time
import uvicorn
from app.database import engine
from app.models.colegio_model import ColegioModel
ColegioModel.__table__.create(bind=engine, checkfirst=True)
servidor = uvicorn.Server(uvicorn.Config('app.main:app', host='127.0.0.1', port={puerto}))
def esperar_cierre():
    while not Path({str(detener)!r}).exists():
        time.sleep(0.05)
    servidor.should_exit = True
threading.Thread(target=esperar_cierre, daemon=True).start()
try:
    servidor.run()
finally:
    engine.dispose()
"""
        with (carpeta / "servidor.log").open("w+", encoding="utf-8") as log:
            # Guarda la salida para mostrar un diagnóstico si falla el arranque.
            proceso = subprocess.Popen(
                [sys.executable, "-c", codigo],
                cwd=Path(__file__).resolve().parents[1] / "backend",
                env=entorno,
                stdout=log,
                stderr=log,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            try:
                # HTTPX llama al servidor por red. trust_env=False evita que
                # un proxy del entorno interfiera con las peticiones locales.
                with httpx.Client(base_url=f"http://127.0.0.1:{puerto}", timeout=2, trust_env=False) as cliente:
                    # Espera a que la app esté lista; falla si no arranca en 15 s.
                    limite = time.monotonic() + 15
                    while True:
                        if proceso.poll() is not None or time.monotonic() >= limite:
                            log.seek(0)
                            self.fail("El servidor no arranco: " + log.read())
                        try:
                            if cliente.get("/openapi.json").status_code == 200:
                                break
                        except httpx.TransportError:
                            pass
                        time.sleep(0.1)
                    # Entrega el cliente al bloque with de la prueba.
                    yield cliente
            finally:
                # Se ejecuta incluso si falla una comprobación, para cerrar el
                # servidor antes de eliminar los archivos temporales en Windows.
                detener.touch()
                try:
                    proceso.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proceso.kill()
                    proceso.wait(timeout=5)

    def test_http_real_y_persistencia_tras_reiniciar(self):
        """Valida rutas, errores y conservación de datos tras reiniciar Uvicorn."""
        # La carpeta y la BD se eliminan automáticamente al salir del bloque.
        with tempfile.TemporaryDirectory(prefix="colegio-test-") as temporal:
            carpeta = Path(temporal)
            # Primera ejecución: comprueba la documentación y las operaciones.
            with self.servidor(carpeta) as cliente:
                self.assertEqual(cliente.get("/docs").status_code, 200)
                self.assertEqual(cliente.get("/").status_code, 200)
                paths = cliente.get("/openapi.json").json()["paths"]
                self.assertTrue({"get", "post"}.issubset(paths["/colegios/"]))
                self.assertTrue({"get", "patch"}.issubset(paths["/colegios/{id_colegio}"]))
                datos = {
                    "nombre": "Colegio HTTP",
                    "direccion": "Calle 1",
                    "representante_legal": "Ana Perez",
                    "telefono_contacto": "3001234567",
                }
                respuesta = cliente.post("/colegios/", json=datos)
                self.assertEqual(respuesta.status_code, 201, respuesta.text)
                colegio = respuesta.json()
                ruta = f"/colegios/{colegio['id']}"
                self.assertEqual(cliente.get(ruta).json(), colegio)
                self.assertEqual(cliente.get("/colegios/").json(), [colegio])
                self.assertEqual(cliente.post("/colegios/", json=datos).status_code, 409)
                self.assertEqual(cliente.patch(ruta, json={"direccion": ""}).status_code, 422)
                self.assertEqual(cliente.get("/colegios/999").status_code, 404)
                respuesta = cliente.patch(ruta, json={"estado_activo": False, "direccion": "Calle 2"})
                self.assertEqual(respuesta.status_code, 200, respuesta.text)
                actualizado = respuesta.json()
                self.assertEqual(actualizado, {**colegio, "estado_activo": False, "direccion": "Calle 2"})
                self.assertEqual(cliente.get("/colegios/").json(), [])
                self.assertEqual(cliente.get("/colegios/?activos_solamente=false").json(), [actualizado])
            # Segunda ejecución: abre la misma BD y verifica los datos guardados.
            with self.servidor(carpeta) as cliente:
                respuesta = cliente.get(ruta)
                self.assertEqual(respuesta.status_code, 200)
                self.assertEqual(respuesta.json(), actualizado)
                respuesta = cliente.patch(ruta, json={"estado_activo": True})
                self.assertEqual(respuesta.status_code, 200)
                self.assertEqual(cliente.get("/colegios/").json(), [respuesta.json()])


if __name__ == "__main__":
    # También permite ejecutar este archivo directamente como script de pruebas.
    unittest.main()
