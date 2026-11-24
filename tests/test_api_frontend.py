"""Endpoints que necesita el frontend: equipos públicos, "mis equipos" y alineaciones con nombres."""
import unittest

from base_api import BasePartidoTest


class ApiFrontendTest(BasePartidoTest):
    def test_equipos_publicos_solo_habilitados_y_sin_sesion(self):
        r = self.client.get(f"/torneos/{self.torneo['id']}/equipos/publico")
        self.assertEqual(r.status_code, 200, r.text)
        nombres = sorted(e["nombre"] for e in r.json())
        self.assertEqual(nombres, [f"Equipo {x}" for x in "ABCDEF"])  # "Sin Pago" (Preinscrito) no aparece
        self.assertEqual(set(r.json()[0]), {"id", "colegio_id", "nombre", "escudo_url"})
        self.assertEqual(self.client.get("/torneos/999/equipos/publico").status_code, 404)

    def test_mis_equipos_del_entrenador(self):
        r = self.client.get("/equipos/mis-equipos", headers=self.h_ent1)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(sorted(e["nombre"] for e in r.json()), ["Equipo A", "Equipo C", "Equipo E"])
        r = self.client.get("/equipos/mis-equipos", headers=self.h_ent2)
        self.assertEqual(len(r.json()), 4)  # B, D, F y "Sin Pago"
        self.assertEqual(self.client.get("/equipos/mis-equipos", headers=self.h_admin).status_code, 403)
        self.assertEqual(self.client.get("/equipos/mis-equipos").status_code, 401)

    def test_alineaciones_con_nombre_y_camiseta(self):
        partido = self.preparar_partido("A", "B")
        r = self.client.get(f"/partidos/{partido['id']}/alineaciones", headers=self.h_arb1)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(len(r.json()), 6)
        primero = r.json()[0]
        self.assertTrue(primero["nombre_completo"].startswith("Jugador"))
        self.assertIn("es_titular", primero)
        self.assertEqual(self.client.get(f"/partidos/{partido['id']}/alineaciones").status_code, 401)


if __name__ == "__main__":
    unittest.main()
