"""Pruebas de Partidos: programación, cruces de horario, reprogramación, árbitro y consultas."""
import unittest
from datetime import datetime

from base_api import BasePartidoTest

from app.repositories.cancha_repository import CanchaRepository
from app.repositories.partido_repository import PartidoRepository
from app.services.cancha_service import CanchaService


class PartidoApiTest(BasePartidoTest):
    # ---------- programar ----------
    def test_programar_partido(self):
        partido = self.programar_ok("A", "B")
        self.assertEqual(partido["estado"], "Programado")
        self.assertEqual(partido["equipo_local_id"], self.eq["A"]["id"])
        self.assertEqual(partido["fecha_hora"], "2026-12-05T10:00:00")
        self.assertIsNone(partido["arbitro_id"])
        # El marcador 0-0 se crea junto con el partido y es público.
        marcador = self.client.get(f"/partidos/{partido['id']}/marcador")
        self.assertEqual(marcador.status_code, 200)
        self.assertEqual((marcador.json()["goles_local"], marcador.json()["goles_visitante"]), (0, 0))
        self.assertFalse(marcador.json()["es_resultado_final"])

    def test_solo_el_administrador_programa_pero_todos_consultan(self):
        partido = self.programar_ok("A", "B")
        datos = {"fase_id": 1, "equipo_local_id": 1, "equipo_visitante_id": 2, "cancha_id": 1, "fecha_hora": "2026-12-05T12:00:00"}
        self.assertEqual(self.client.post("/partidos/", json=datos).status_code, 401)
        self.assertEqual(self.client.post("/partidos/", json=datos, headers=self.h_ent1).status_code, 403)
        self.assertEqual(self.client.post("/partidos/", json=datos, headers=self.h_arb1).status_code, 403)
        self.assertEqual(self.client.get(f"/partidos/{partido['id']}").json(), partido)  # sin sesión
        self.assertEqual(self.client.get("/partidos/999").status_code, 404)
        self.assertEqual(self.client.get("/partidos/999/marcador").status_code, 404)

    def test_validaciones_de_esquema(self):
        base = {
            "fase_id": self.fase_grupos["id"], "equipo_local_id": self.eq["A"]["id"],
            "equipo_visitante_id": self.eq["B"]["id"], "cancha_id": self.cancha1["id"],
            "fecha_hora": "2026-12-05T10:00:00",
        }
        for cambio in (
            {"equipo_visitante_id": self.eq["A"]["id"]},  # contra sí mismo
            {"fecha_hora": "2026-12-05T10:00:00Z"},  # con zona horaria
            {"fecha_hora": "no-es-fecha"},
            {"campo_raro": 1},
        ):
            r = self.client.post("/partidos/", json={**base, **cambio}, headers=self.h_admin)
            self.assertEqual(r.status_code, 422, cambio)

    def test_fase_y_torneo(self):
        self.assertEqual(self.programar("A", "B", fase={"id": 999}).status_code, 404)
        # Un torneo que aún está en Inscripciones no programa partidos.
        otro = self.crear_torneo_api(nombre="Otra Copa")
        fase = self.client.post(
            f"/torneos/{otro['id']}/fases", json={"nombre": "Grupos", "tipo_formato": "Grupos"}, headers=self.h_admin
        ).json()
        self.assertEqual(self.programar("A", "B", fase=fase).status_code, 409)

    def test_una_fase_espera_a_que_termine_la_anterior(self):
        r = self.programar("A", "B", fase=self.fase_final)
        self.assertEqual(r.status_code, 409)
        self.assertIn("Fase de Grupos", r.json()["detail"])

    def test_equipos_validos(self):
        self.assertEqual(self.programar("A", 999).status_code, 404)
        self.assertEqual(self.programar("A", self.eq_pre).status_code, 400)  # Preinscrito
        # En fase de grupos deben compartir grupo: D está en el Grupo B y F no tiene grupo.
        self.assertEqual(self.programar("A", "D").status_code, 400)
        self.assertEqual(self.programar("A", "F").status_code, 400)
        self.assertEqual(self.programar("D", "E").status_code, 201)

    def test_pareja_repetida_en_la_fase(self):
        self.programar_ok("A", "B")
        r = self.programar("B", "A", hora="2026-12-07T10:00:00", cancha=self.cancha2)
        self.assertEqual(r.status_code, 409)

    def test_fecha_dentro_del_torneo(self):
        self.assertEqual(self.programar("A", "B", hora="2026-11-30T10:00:00").status_code, 400)
        self.assertEqual(self.programar("A", "B", hora="2026-12-21T10:00:00").status_code, 400)
        self.assertEqual(self.programar("A", "B", hora="2026-12-20T18:00:00").status_code, 201)

    # ---------- cruces de horario ----------
    def test_cancha_ocupada(self):
        self.programar_ok("A", "B")  # 10:00 en la cancha 1
        self.assertEqual(self.programar("D", "E", hora="2026-12-05T10:30:00").status_code, 409)
        self.assertEqual(self.programar("D", "E", hora="2026-12-05T10:30:00", cancha=self.cancha2).status_code, 201)

    def test_cancha_inhabilitada_o_inexistente(self):
        self.client.patch(f"/canchas/{self.cancha2['id']}/estado", json={"estado_activo": False}, headers=self.h_admin)
        self.assertEqual(self.programar("A", "B", cancha=self.cancha2).status_code, 409)
        self.assertEqual(self.programar("A", "B", cancha={"id": 999}).status_code, 404)

    def test_un_equipo_no_juega_dos_partidos_a_la_vez(self):
        self.programar_ok("A", "B")  # 10:00-11:30
        r = self.programar("A", "C", hora="2026-12-05T10:30:00", cancha=self.cancha2)
        self.assertEqual(r.status_code, 409)
        # A la hora exacta en que termina el anterior ya es válido.
        r = self.programar("A", "C", hora="2026-12-05T11:30:00", cancha=self.cancha2)
        self.assertEqual(r.status_code, 201, r.text)

    def test_arbitro_al_programar(self):
        self.assertEqual(self.programar("A", "B", arbitro_id=999).status_code, 404)
        self.assertEqual(self.programar("A", "B", arbitro_id=self.ent1_id).status_code, 400)  # no es árbitro
        partido = self.programar_ok("A", "B", arbitro_id=self.arb1_id)
        self.assertEqual(partido["arbitro_id"], self.arb1_id)
        # El mismo árbitro no puede estar en dos partidos a la vez.
        r = self.programar("D", "E", hora="2026-12-05T10:30:00", cancha=self.cancha2, arbitro_id=self.arb1_id)
        self.assertEqual(r.status_code, 409)
        r = self.programar("D", "E", hora="2026-12-05T10:30:00", cancha=self.cancha2, arbitro_id=self.arb2_id)
        self.assertEqual(r.status_code, 201, r.text)

    # ---------- reprogramar y suspender ----------
    def test_reprogramar(self):
        partido = self.programar_ok("A", "B")
        ruta = f"/partidos/{partido['id']}/reprogramar"
        cuerpo = {"fecha_hora": "2026-12-06T09:00:00", "cancha_id": self.cancha2["id"]}
        self.assertEqual(self.client.patch(ruta, json=cuerpo, headers=self.h_ent1).status_code, 403)
        r = self.client.patch(ruta, json=cuerpo, headers=self.h_admin)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["fecha_hora"], "2026-12-06T09:00:00")
        self.assertEqual(r.json()["cancha_id"], self.cancha2["id"])
        # Sin cancha_id se conserva la actual, y reprogramarlo al mismo horario no choca consigo mismo.
        r = self.client.patch(ruta, json={"fecha_hora": "2026-12-06T09:00:00"}, headers=self.h_admin)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["cancha_id"], self.cancha2["id"])

    def test_reprogramar_valida_cruces_y_fechas(self):
        self.programar_ok("A", "B")  # 10:00, cancha 1
        otro = self.programar_ok("D", "E", hora="2026-12-05T14:00:00")
        ruta = f"/partidos/{otro['id']}/reprogramar"
        self.assertEqual(self.client.patch(ruta, json={"fecha_hora": "2026-12-05T10:30:00"}, headers=self.h_admin).status_code, 409)
        self.assertEqual(self.client.patch(ruta, json={"fecha_hora": "2026-12-25T10:00:00"}, headers=self.h_admin).status_code, 400)
        self.assertEqual(self.client.patch("/partidos/999/reprogramar", json={"fecha_hora": "2026-12-05T10:30:00"}, headers=self.h_admin).status_code, 404)

    def test_suspender_libera_el_horario(self):
        partido = self.programar_ok("A", "B")
        ruta = f"/partidos/{partido['id']}/suspender"
        self.assertEqual(self.client.post(ruta, headers=self.h_ent1).status_code, 403)
        r = self.client.post(ruta, headers=self.h_admin)
        self.assertEqual(r.json()["estado"], "Suspendido")
        self.assertEqual(self.client.post(ruta, headers=self.h_admin).status_code, 409)

        self.programar_ok("D", "E")  # ahora la cancha 1 a las 10:00 está libre
        reprogramar = f"/partidos/{partido['id']}/reprogramar"
        r = self.client.patch(reprogramar, json={"fecha_hora": "2026-12-05T10:00:00"}, headers=self.h_admin)
        self.assertEqual(r.status_code, 409)  # ya la usa otro partido
        r = self.client.patch(reprogramar, json={"fecha_hora": "2026-12-06T10:00:00"}, headers=self.h_admin)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["estado"], "Programado")

    # ---------- árbitro ----------
    def test_asignar_arbitro(self):
        partido = self.programar_ok("A", "B")
        ruta = f"/partidos/{partido['id']}/arbitro"
        self.assertEqual(self.client.put(ruta, json={"arbitro_id": self.arb1_id}, headers=self.h_ent1).status_code, 403)
        r = self.client.put(ruta, json={"arbitro_id": self.arb1_id}, headers=self.h_admin)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["arbitro_id"], self.arb1_id)
        self.assertEqual(self.client.put(ruta, json={"arbitro_id": self.ent1_id}, headers=self.h_admin).status_code, 400)
        self.assertEqual(self.client.put(ruta, json={"arbitro_id": 999}, headers=self.h_admin).status_code, 404)

    def test_asignar_arbitro_ocupado_o_partido_suspendido(self):
        self.programar_ok("A", "B", arbitro_id=self.arb1_id)
        otro = self.programar_ok("D", "E", hora="2026-12-05T10:30:00", cancha=self.cancha2)
        ruta = f"/partidos/{otro['id']}/arbitro"
        self.assertEqual(self.client.put(ruta, json={"arbitro_id": self.arb1_id}, headers=self.h_admin).status_code, 409)
        self.client.post(f"/partidos/{otro['id']}/suspender", headers=self.h_admin)
        self.assertEqual(self.client.put(ruta, json={"arbitro_id": self.arb2_id}, headers=self.h_admin).status_code, 409)

    def test_mis_asignaciones(self):
        partido = self.programar_ok("A", "B", arbitro_id=self.arb1_id)
        self.programar_ok("D", "E", cancha=self.cancha2)  # sin árbitro
        r = self.client.get("/partidos/mis-asignaciones", headers=self.h_arb1)
        self.assertEqual([p["id"] for p in r.json()], [partido["id"]])
        self.assertEqual(self.client.get("/partidos/mis-asignaciones", headers=self.h_arb2).json(), [])
        self.assertEqual(self.client.get("/partidos/mis-asignaciones", headers=self.h_ent1).status_code, 403)
        self.assertEqual(self.client.get("/partidos/mis-asignaciones").status_code, 401)

    # ---------- consultas ----------
    def test_calendario_de_la_fase_es_publico_y_ordenado(self):
        tarde = self.programar_ok("A", "B", hora="2026-12-08T16:00:00")
        temprano = self.programar_ok("A", "C", hora="2026-12-05T09:00:00", cancha=self.cancha2)
        r = self.client.get(f"/fases/{self.fase_grupos['id']}/partidos")
        self.assertEqual([p["id"] for p in r.json()], [temprano["id"], tarde["id"]])
        self.assertEqual(self.client.get("/fases/999/partidos").status_code, 404)

    def test_calendario_del_equipo(self):
        ab = self.programar_ok("A", "B")
        ac = self.programar_ok("C", "A", hora="2026-12-06T10:00:00")
        self.programar_ok("D", "E", cancha=self.cancha2)
        ruta = f"/equipos/{self.eq['A']['id']}/calendario"
        r = self.client.get(ruta, headers=self.h_ent1)
        self.assertEqual([p["id"] for p in r.json()], [ab["id"], ac["id"]])  # local o visitante
        self.assertEqual(self.client.get(ruta, headers=self.h_admin).status_code, 200)
        self.assertEqual(self.client.get(ruta, headers=self.h_ent2).status_code, 403)
        self.assertEqual(self.client.get(ruta).status_code, 401)
        self.assertEqual(self.client.get("/equipos/999/calendario", headers=self.h_admin).status_code, 404)

    def test_agenda_de_la_cancha(self):
        partido = self.programar_ok("A", "B")
        self.programar_ok("D", "E", cancha=self.cancha2)
        ruta = f"/canchas/{self.cancha1['id']}/agenda"
        r = self.client.get(ruta + "?fecha=2026-12-05", headers=self.h_ent1)
        self.assertEqual([p["id"] for p in r.json()], [partido["id"]])
        self.assertEqual(self.client.get(ruta + "?fecha=2026-12-06", headers=self.h_ent1).json(), [])
        self.assertEqual(self.client.get(ruta + "?fecha=2026-12-05").status_code, 401)
        self.assertEqual(self.client.get(ruta, headers=self.h_ent1).status_code, 422)  # falta la fecha
        self.assertEqual(self.client.get("/canchas/999/agenda?fecha=2026-12-05", headers=self.h_ent1).status_code, 404)

    def test_verificar_disponibilidad_de_la_cancha(self):
        self.programar_ok("A", "B")
        id_cancha = self.cancha1["id"]
        with self.Sesion() as db:
            servicio = CanchaService(CanchaRepository(db), PartidoRepository(db))
            self.assertFalse(servicio.verificar_disponibilidad(id_cancha, datetime(2026, 12, 5, 10, 30), 90))
            self.assertTrue(servicio.verificar_disponibilidad(id_cancha, datetime(2026, 12, 5, 11, 30), 90))
            self.assertTrue(servicio.verificar_disponibilidad(id_cancha, datetime(2026, 12, 5, 10, 30), 90, excluir_partido_id=1))
            self.assertTrue(servicio.verificar_disponibilidad(self.cancha2["id"], datetime(2026, 12, 5, 10, 30)))


if __name__ == "__main__":
    unittest.main()
