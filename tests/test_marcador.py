"""Pruebas de la entidad Marcador: nace 0-0, lo mueven los eventos y se congela al cerrar el acta."""
import unittest

from base_api import BasePartidoTest


class MarcadorApiTest(BasePartidoTest):
    def marcador(self, partido):
        r = self.client.get(f"/partidos/{partido['id']}/marcador")
        self.assertEqual(r.status_code, 200)
        return r.json()

    def gol(self, partido, letra, indice=0, h=None):
        return self.client.post(
            f"/partidos/{partido['id']}/eventos",
            json={"equipo_id": self.eq[letra]["id"], "jugador_id": self.ids_jugadores(letra)[indice],
                  "tipo_evento": "Gol", "minuto_ocurrencia": 10},
            headers=h or self.h_arb1,
        )

    def test_nace_en_cero_y_es_publico(self):
        partido = self.programar_ok("A", "B")
        m = self.marcador(partido)
        self.assertEqual((m["goles_local"], m["goles_visitante"], m["es_resultado_final"]), (0, 0, False))
        self.assertIsNone(m["goles_penales_local"])
        self.assertEqual(self.client.get("/partidos/999/marcador").status_code, 404)

    def test_los_goles_suman_al_equipo_correcto(self):
        partido = self.preparar_partido("A", "B")
        self.iniciar(partido)
        self.assertEqual(self.gol(partido, "A").status_code, 201)
        self.assertEqual(self.gol(partido, "B").status_code, 201)
        self.assertEqual(self.gol(partido, "B", 1).status_code, 201)
        m = self.marcador(partido)
        self.assertEqual((m["goles_local"], m["goles_visitante"]), (1, 2))

    def test_borrar_un_evento_revierte_el_gol(self):
        partido = self.preparar_partido("A", "B")
        self.iniciar(partido)
        evento = self.gol(partido, "A").json()
        r = self.client.delete(f"/partidos/{partido['id']}/eventos/{evento['id']}", headers=self.h_arb1)
        self.assertEqual(r.status_code, 204, r.text)
        self.assertEqual(self.marcador(partido)["goles_local"], 0)

    def test_acta_cerrada_congela_el_marcador(self):
        partido = self.preparar_partido("A", "B")
        self.terminar_partido(partido, 3, 1)
        m = self.marcador(partido)
        self.assertTrue(m["es_resultado_final"])
        r = self.client.put(f"/partidos/{partido['id']}/marcador", json={"goles_local": 0, "goles_visitante": 0}, headers=self.h_arb1)
        self.assertEqual(r.status_code, 409)
        self.assertEqual(self.gol(partido, "A").status_code, 409)
        self.assertEqual(self.marcador(partido)["goles_local"], 3)

    def test_penales_solo_en_eliminatoria(self):
        partido = self.preparar_partido("A", "B")
        self.iniciar(partido)
        cuerpo = {"goles_local": 1, "goles_visitante": 1, "goles_penales_local": 4, "goles_penales_visitante": 3}
        r = self.client.put(f"/partidos/{partido['id']}/marcador", json=cuerpo, headers=self.h_arb1)
        self.assertEqual(r.status_code, 400)
        incompleto = {**cuerpo}
        del incompleto["goles_penales_visitante"]
        r = self.client.put(f"/partidos/{partido['id']}/marcador", json=incompleto, headers=self.h_arb1)
        self.assertEqual(r.status_code, 422)


if __name__ == "__main__":
    unittest.main()
