"""Pruebas de Alineaciones: planilla del entrenador, reglas del torneo y elegibilidad de jugadores."""
import unittest
from types import SimpleNamespace

from base_api import BasePartidoTest
from fastapi import HTTPException

from app.core.dependencies import get_alineacion_service
from app.schemas.alineacion_schema import JugadorConvocado
from app.services.alineacion_service import AlineacionService


class AlineacionApiTest(BasePartidoTest):
    def setUp(self):
        super().setUp()
        self.partido = self.programar_ok("A", "B")
        self.ruta_a = self.ruta("A")

    def ruta(self, letra, partido=None):
        return f"/partidos/{(partido or self.partido)['id']}/equipos/{self.eq[letra]['id']}/alineacion"

    @staticmethod
    def planilla(ids, titulares=2, **camisetas):
        """Los primeros `titulares` jugadores arrancan; el resto va al banco."""
        return {
            "jugadores": [
                {"jugador_id": id_jugador, "es_titular": indice < titulares, **camisetas.get(str(indice), {})}
                for indice, id_jugador in enumerate(ids)
            ]
        }

    def enviar(self, letra, cuerpo, h=None, partido=None):
        return self.client.put(self.ruta(letra, partido), json=cuerpo, headers=h or self.h_ent1)

    def guardadas(self, partido=None):
        r = self.client.get(f"/partidos/{(partido or self.partido)['id']}/alineaciones", headers=self.h_admin)
        self.assertEqual(r.status_code, 200)
        return r.json()

    # ---------- envío ----------
    def test_enviar_planilla(self):
        ids = self.ids_jugadores("A")
        r = self.enviar("A", self.planilla(ids))
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(len(r.json()), 3)
        self.assertEqual([a["es_titular"] for a in r.json()], [True, True, False])
        self.assertTrue(all(a["equipo_id"] == self.eq["A"]["id"] for a in r.json()))
        # Cualquier usuario con sesión puede ver las alineaciones; sin sesión no.
        ruta = f"/partidos/{self.partido['id']}/alineaciones"
        self.assertEqual(len(self.client.get(ruta, headers=self.h_ent2).json()), 3)
        self.assertEqual(self.client.get(ruta).status_code, 401)

    def test_solo_el_entrenador_dueno_envia(self):
        cuerpo = self.planilla(self.ids_jugadores("A"))
        self.assertEqual(self.enviar("A", cuerpo, h=self.h_ent2).status_code, 403)
        self.assertEqual(self.enviar("A", cuerpo, h=self.h_admin).status_code, 403)
        self.assertEqual(self.enviar("A", cuerpo, h=self.h_arb1).status_code, 403)
        self.assertEqual(self.client.put(self.ruta_a, json=cuerpo).status_code, 401)
        self.assertEqual(self.guardadas(), [])

    def test_reglas_de_la_planilla(self):
        ids = self.ids_jugadores("A")
        self.assertEqual(self.enviar("A", self.planilla(ids, titulares=1)).status_code, 400)  # faltan titulares
        self.assertEqual(self.enviar("A", self.planilla(ids, titulares=3)).status_code, 400)  # sobran titulares
        repetido = {"jugadores": [{"jugador_id": ids[0], "es_titular": True}, {"jugador_id": ids[0], "es_titular": True}]}
        self.assertEqual(self.enviar("A", repetido).status_code, 400)
        camisetas = self.planilla(ids, **{"0": {"numero_camiseta": 9}, "1": {"numero_camiseta": 9}})
        self.assertEqual(self.enviar("A", camisetas).status_code, 400)
        self.assertEqual(self.enviar("A", {"jugadores": []}).status_code, 422)
        self.assertEqual(self.guardadas(), [])

    def test_maximo_de_suplentes(self):
        torneo = SimpleNamespace(reglas={"titulares": 1, "max_suplentes": 1})
        convocados = [JugadorConvocado(jugador_id=i, es_titular=(i == 1)) for i in (1, 2, 3)]  # 1 titular, 2 suplentes
        with self.assertRaises(HTTPException) as contexto:
            AlineacionService.validar_reglas_plantilla(convocados, torneo)
        self.assertEqual(contexto.exception.status_code, 400)
        AlineacionService.validar_reglas_plantilla(convocados[:2], torneo)  # 1 titular y 1 suplente: válido

    # ---------- elegibilidad ----------
    def test_jugador_sancionado_rechaza_toda_la_planilla(self):
        ids = self.ids_jugadores("A")
        self.client.patch(f"/jugadores/{ids[1]}/sancion", json={"sancionado": True}, headers=self.h_admin)
        r = self.enviar("A", self.planilla(ids))
        self.assertEqual(r.status_code, 400)
        self.assertIn("inhabilitado", r.json()["detail"])
        self.assertEqual(self.guardadas(), [])  # no se guardó nada

    def test_jugadores_de_otro_equipo_o_inexistentes(self):
        ids_a, ids_b = self.ids_jugadores("A"), self.ids_jugadores("B")
        r = self.enviar("A", self.planilla([ids_a[0], ids_b[0], ids_a[1]]))
        self.assertEqual(r.status_code, 400)
        self.assertIn("no pertenece", r.json()["detail"])
        self.assertEqual(self.enviar("A", self.planilla([ids_a[0], 999])).status_code, 400)
        self.assertEqual(self.guardadas(), [])

    # ---------- reemplazo ----------
    def test_reenviar_reemplaza_la_planilla(self):
        ids = self.ids_jugadores("A")
        self.enviar("A", self.planilla(ids))
        nueva = {"jugadores": [
            {"jugador_id": ids[1], "es_titular": True, "numero_camiseta": 7},
            {"jugador_id": ids[2], "es_titular": True},
        ]}
        r = self.enviar("A", nueva)
        self.assertEqual(r.status_code, 200, r.text)
        guardadas = self.guardadas()
        self.assertEqual({a["jugador_id"] for a in guardadas}, {ids[1], ids[2]})
        self.assertEqual(next(a for a in guardadas if a["jugador_id"] == ids[1])["numero_camiseta"], 7)

    def test_cada_equipo_tiene_su_planilla(self):
        self.enviar("A", self.planilla(self.ids_jugadores("A")))
        self.enviar("B", self.planilla(self.ids_jugadores("B")), h=self.h_ent2)
        guardadas = self.guardadas()
        self.assertEqual(len(guardadas), 6)
        self.assertEqual({a["equipo_id"] for a in guardadas}, {self.eq["A"]["id"], self.eq["B"]["id"]})

    # ---------- estado del partido y existencia ----------
    def test_equipo_que_no_juega_el_partido(self):
        r = self.enviar("C", self.planilla(self.ids_jugadores("C")))  # C es del entrenador 1 pero juega A-B
        self.assertEqual(r.status_code, 400)

    def test_partido_que_no_esta_programado(self):
        self.client.post(f"/partidos/{self.partido['id']}/suspender", headers=self.h_admin)
        self.assertEqual(self.enviar("A", self.planilla(self.ids_jugadores("A"))).status_code, 409)

    def test_recursos_inexistentes(self):
        cuerpo = self.planilla(self.ids_jugadores("A"))
        self.assertEqual(self.client.put(f"/partidos/999/equipos/{self.eq['A']['id']}/alineacion", json=cuerpo, headers=self.h_ent1).status_code, 404)
        self.assertEqual(self.client.put(f"/partidos/{self.partido['id']}/equipos/999/alineacion", json=cuerpo, headers=self.h_ent1).status_code, 404)
        self.assertEqual(self.client.get("/partidos/999/alineaciones", headers=self.h_admin).status_code, 404)

    # ---------- validar_alineaciones ----------
    def test_validar_alineaciones(self):
        def listas():
            with self.Sesion() as db:
                return get_alineacion_service(db).validar_alineaciones(self.partido["id"])

        self.assertFalse(listas())
        self.enviar("A", self.planilla(self.ids_jugadores("A")))
        self.assertFalse(listas())  # falta B: se podría decretar W.O.
        self.enviar("B", self.planilla(self.ids_jugadores("B")), h=self.h_ent2)
        self.assertTrue(listas())


if __name__ == "__main__":
    unittest.main()
