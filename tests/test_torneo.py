"""Pruebas de Torneos y Fases: permisos, ciclo de estados y estructura de fases."""
import unittest

from base_api import BaseApiTest

from app.core.enums import EstadoTorneoEnum
from app.repositories.torneo_repository import TorneoRepository


class TorneoApiTest(BaseApiTest):
    def setUp(self):
        super().setUp()
        self.datos = {
            "nombre": "Copa Intercolegial 2026",
            "categoria": "Sub-17",
            "fecha_inicio": "2026-12-01",
            "fecha_fin": "2026-12-20",
            "reglas": {"puntos_victoria": 3, "max_jugadores": 18},
        }

    def crear(self, **cambios):
        r = self.client.post("/torneos/", json={**self.datos, **cambios}, headers=self.h_admin)
        self.assertEqual(r.status_code, 201, r.text)
        return r.json()

    def poner_estado(self, id_torneo, estado):
        """Fuerza un estado directo en la BD (iniciar_torneo llega con la Fase 3)."""
        with self.Sesion() as db:
            TorneoRepository(db).actualizar_estado(id_torneo, estado)

    def post_admin(self, ruta, **kw):
        return self.client.post(ruta, headers=self.h_admin, **kw)

    # ---------- torneos ----------
    def test_crear_nace_en_inscripciones_y_guarda_reglas(self):
        torneo = self.crear()
        self.assertEqual(torneo["estado"], "Inscripciones")
        self.assertEqual(torneo["reglas"], {"puntos_victoria": 3, "max_jugadores": 18})
        self.assertEqual(torneo["fecha_inicio"], "2026-12-01")

    def test_consulta_publica_pero_modificar_exige_administrador(self):
        torneo = self.crear()
        # Sin sesión (espectador): puede consultar.
        self.assertEqual(self.client.get("/torneos/").json(), [torneo])
        self.assertEqual(self.client.get(f"/torneos/{torneo['id']}").json(), torneo)
        # Pero no modificar.
        self.assertEqual(self.client.post("/torneos/", json=self.datos).status_code, 401)
        self.assertEqual(self.client.patch(f"/torneos/{torneo['id']}", json={"nombre": "X"}).status_code, 401)
        self.assertEqual(self.client.post(f"/torneos/{torneo['id']}/cancelar").status_code, 401)

        self.crear_usuario("Entrenador", "ent@torneo.edu.co")
        h = self.cabecera("ent@torneo.edu.co")
        self.assertEqual(self.client.post("/torneos/", json=self.datos, headers=h).status_code, 403)
        self.assertEqual(self.client.post(f"/torneos/{torneo['id']}/finalizar", headers=h).status_code, 403)

    def test_fechas_invalidas(self):
        r = self.client.post("/torneos/", json={**self.datos, "fecha_fin": "2026-11-30"}, headers=self.h_admin)
        self.assertEqual(r.status_code, 422)
        torneo = self.crear()
        # Solo se envía fecha_fin, pero se compara con la fecha_inicio guardada.
        r = self.client.patch(f"/torneos/{torneo['id']}", json={"fecha_fin": "2026-11-30"}, headers=self.h_admin)
        self.assertEqual(r.status_code, 422)

    def test_filtrar_por_estado(self):
        activo = self.crear()
        cancelado = self.crear(nombre="Copa Vieja")
        self.post_admin(f"/torneos/{cancelado['id']}/cancelar")
        r = self.client.get("/torneos/?estado=Cancelado")
        self.assertEqual([t["id"] for t in r.json()], [cancelado["id"]])
        r = self.client.get("/torneos/?estado=Inscripciones")
        self.assertEqual([t["id"] for t in r.json()], [activo["id"]])
        self.assertEqual(self.client.get("/torneos/?estado=Inventado").status_code, 422)

    def test_actualizar_detalles_en_inscripciones(self):
        torneo = self.crear()
        r = self.client.patch(
            f"/torneos/{torneo['id']}",
            json={"nombre": "Copa Renovada", "fecha_fin": "2026-12-30", "reglas": None},
            headers=self.h_admin,
        )
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json(), {**torneo, "nombre": "Copa Renovada", "fecha_fin": "2026-12-30", "reglas": None})
        r = self.client.patch(f"/torneos/{torneo['id']}", json={"estado": "En_Curso"}, headers=self.h_admin)
        self.assertEqual(r.status_code, 422)  # el estado no se cambia por PATCH
        r = self.client.patch(f"/torneos/{torneo['id']}", json={"nombre": None}, headers=self.h_admin)
        self.assertEqual(r.status_code, 422)

    def test_cancelar_y_luego_nada_se_puede_cambiar(self):
        torneo = self.crear()
        r = self.post_admin(f"/torneos/{torneo['id']}/cancelar")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["estado"], "Cancelado")
        self.assertEqual(self.post_admin(f"/torneos/{torneo['id']}/cancelar").status_code, 409)
        self.assertEqual(self.post_admin(f"/torneos/{torneo['id']}/finalizar").status_code, 409)
        r = self.client.patch(f"/torneos/{torneo['id']}", json={"nombre": "X"}, headers=self.h_admin)
        self.assertEqual(r.status_code, 409)

    def test_finalizar_solo_desde_en_curso(self):
        torneo = self.crear()
        self.assertEqual(self.post_admin(f"/torneos/{torneo['id']}/finalizar").status_code, 409)
        self.poner_estado(torneo["id"], EstadoTorneoEnum.EN_CURSO)
        r = self.post_admin(f"/torneos/{torneo['id']}/finalizar")
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["estado"], "Finalizado")
        # Un torneo finalizado ya no se modifica ni se cancela.
        self.assertEqual(self.post_admin(f"/torneos/{torneo['id']}/cancelar").status_code, 409)
        self.assertEqual(
            self.client.patch(f"/torneos/{torneo['id']}", json={"nombre": "X"}, headers=self.h_admin).status_code, 409
        )

    def test_cancelar_un_torneo_en_curso(self):
        torneo = self.crear()
        self.poner_estado(torneo["id"], EstadoTorneoEnum.EN_CURSO)
        self.assertEqual(self.post_admin(f"/torneos/{torneo['id']}/cancelar").json()["estado"], "Cancelado")

    def test_torneo_inexistente(self):
        self.assertEqual(self.client.get("/torneos/999").status_code, 404)
        self.assertEqual(self.client.patch("/torneos/999", json={"nombre": "X"}, headers=self.h_admin).status_code, 404)
        self.assertEqual(self.post_admin("/torneos/999/cancelar").status_code, 404)
        self.assertEqual(self.post_admin("/torneos/999/finalizar").status_code, 404)

    # ---------- fases ----------
    def fase(self, nombre="Fase de Grupos", tipo="Grupos"):
        return {"nombre": nombre, "tipo_formato": tipo}

    def test_crear_fase_y_listar_publicamente(self):
        torneo = self.crear()
        ruta = f"/torneos/{torneo['id']}/fases"
        r = self.post_admin(ruta, json=self.fase())
        self.assertEqual(r.status_code, 201, r.text)
        fase = r.json()
        self.assertEqual(fase["estado"], "Programada")
        self.assertEqual(fase["torneo_id"], torneo["id"])
        self.assertEqual(fase["tipo_formato"], "Grupos")
        self.assertEqual(self.client.get(ruta).json(), [fase])  # sin sesión
        self.assertEqual(self.client.get(f"/fases/{fase['id']}").json(), fase)

    def test_fase_nombre_duplicado_en_el_mismo_torneo(self):
        torneo = self.crear()
        ruta = f"/torneos/{torneo['id']}/fases"
        self.post_admin(ruta, json=self.fase())
        self.assertEqual(self.post_admin(ruta, json=self.fase()).status_code, 409)
        # El mismo nombre es válido en otro torneo.
        otro = self.crear(nombre="Otra Copa")
        self.assertEqual(self.post_admin(f"/torneos/{otro['id']}/fases", json=self.fase()).status_code, 201)

    def test_crear_fase_exige_administrador_y_torneo_en_inscripciones(self):
        torneo = self.crear()
        ruta = f"/torneos/{torneo['id']}/fases"
        self.assertEqual(self.client.post(ruta, json=self.fase()).status_code, 401)
        self.crear_usuario("Arbitro", "arb@torneo.edu.co")
        h = self.cabecera("arb@torneo.edu.co")
        self.assertEqual(self.client.post(ruta, json=self.fase(), headers=h).status_code, 403)

        self.assertEqual(self.post_admin("/torneos/999/fases", json=self.fase()).status_code, 404)
        self.post_admin(f"/torneos/{torneo['id']}/cancelar")
        self.assertEqual(self.post_admin(ruta, json=self.fase()).status_code, 409)

    def test_estructurar_fases_en_orden(self):
        torneo = self.crear()
        ruta = f"/torneos/{torneo['id']}/fases/estructurar"
        config = {
            "fases": [
                self.fase("Fase de Grupos", "Grupos"),
                self.fase("Cuartos de Final", "Eliminatoria_Directa"),
                self.fase("Final", "Eliminatoria_Directa"),
            ]
        }
        r = self.post_admin(ruta, json=config)
        self.assertEqual(r.status_code, 201, r.text)
        self.assertEqual([f["nombre"] for f in r.json()], ["Fase de Grupos", "Cuartos de Final", "Final"])
        self.assertTrue(all(f["estado"] == "Programada" for f in r.json()))
        listado = self.client.get(f"/torneos/{torneo['id']}/fases").json()
        self.assertEqual([f["nombre"] for f in listado], ["Fase de Grupos", "Cuartos de Final", "Final"])
        # Ya tiene fases: no se vuelve a estructurar.
        self.assertEqual(self.post_admin(ruta, json=config).status_code, 409)

    def test_estructurar_validaciones(self):
        torneo = self.crear()
        ruta = f"/torneos/{torneo['id']}/fases/estructurar"
        self.assertEqual(self.post_admin(ruta, json={"fases": []}).status_code, 422)
        repetidas = {"fases": [self.fase("A"), self.fase("A")]}
        self.assertEqual(self.post_admin(ruta, json=repetidas).status_code, 422)
        formato_malo = {"fases": [self.fase("A", "Liga")]}
        self.assertEqual(self.post_admin(ruta, json=formato_malo).status_code, 422)
        # Nada de lo anterior debe haber dejado fases creadas.
        self.assertEqual(self.client.get(f"/torneos/{torneo['id']}/fases").json(), [])
        self.assertEqual(self.client.post(ruta, json={"fases": [self.fase()]}).status_code, 401)

    def test_fases_de_torneo_o_fase_inexistente(self):
        self.assertEqual(self.client.get("/torneos/999/fases").status_code, 404)
        self.assertEqual(self.client.get("/fases/999").status_code, 404)


if __name__ == "__main__":
    unittest.main()
