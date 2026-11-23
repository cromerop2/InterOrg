"""Pruebas del día del partido: inicio, marcador, cierre de acta y W.O."""
import unittest

from base_api import BasePartidoTest


class JuegoApiTest(BasePartidoTest):
    def estado_fase(self):
        return self.client.get(f"/fases/{self.fase_grupos['id']}").json()["estado"]

    # ---------- iniciar ----------
    def test_iniciar_partido(self):
        partido = self.preparar_partido("A", "B")
        self.assertEqual(self.estado_fase(), "Programada")
        r = self.iniciar(partido)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["estado"], "En_Juego")
        self.assertEqual(self.estado_fase(), "En_Juego")  # la fase arranca con su primer partido
        self.assertEqual(self.iniciar(partido).status_code, 409)

    def test_solo_el_arbitro_designado_inicia(self):
        partido = self.preparar_partido("A", "B")
        self.assertEqual(self.iniciar(partido, h=self.h_arb2).status_code, 403)
        self.assertEqual(self.iniciar(partido, h=self.h_admin).status_code, 403)
        self.assertEqual(self.iniciar(partido, h=self.h_ent1).status_code, 403)
        self.assertEqual(self.client.post(f"/partidos/{partido['id']}/iniciar").status_code, 401)
        self.assertEqual(self.client.post("/partidos/999/iniciar", headers=self.h_arb1).status_code, 404)

    def test_sin_arbitro_asignado_nadie_inicia(self):
        partido = self.preparar_partido("A", "B", arbitro=False)
        self.assertEqual(self.iniciar(partido).status_code, 403)

    def test_iniciar_exige_las_dos_alineaciones(self):
        partido = self.preparar_partido("A", "B", alineaciones=False)
        self.assertEqual(self.iniciar(partido).status_code, 409)
        self.enviar_planilla(partido, "A")
        r = self.iniciar(partido)
        self.assertEqual(r.status_code, 409)
        self.assertIn("W.O.", r.json()["detail"])
        self.enviar_planilla(partido, "B")
        self.assertEqual(self.iniciar(partido).status_code, 200)
        self.assertEqual(self.estado_fase(), "En_Juego")

    # ---------- marcador ----------
    def test_registrar_marcador(self):
        partido = self.preparar_partido("A", "B")
        ruta = f"/partidos/{partido['id']}/marcador"
        cuerpo = {"goles_local": 2, "goles_visitante": 1}
        self.assertEqual(self.client.put(ruta, json=cuerpo, headers=self.h_arb1).status_code, 409)  # aún Programado
        self.iniciar(partido)
        self.assertEqual(self.client.put(ruta, json=cuerpo, headers=self.h_arb2).status_code, 403)
        self.assertEqual(self.client.put(ruta, json=cuerpo, headers=self.h_admin).status_code, 403)
        r = self.client.put(ruta, json=cuerpo, headers=self.h_arb1)
        self.assertEqual(r.status_code, 200, r.text)
        marcador = self.client.get(ruta).json()
        self.assertEqual((marcador["goles_local"], marcador["goles_visitante"]), (2, 1))
        self.assertFalse(marcador["es_resultado_final"])

    def test_validaciones_del_marcador(self):
        partido = self.preparar_partido("A", "B")
        self.iniciar(partido)
        ruta = f"/partidos/{partido['id']}/marcador"
        for malo in (
            {"goles_local": -1, "goles_visitante": 0},
            {"goles_local": 1},
            {"goles_local": 1, "goles_visitante": 0, "goles_penales_local": 3},  # penales a medias
            {"goles_local": 1, "goles_visitante": 0, "campo_raro": 1},
        ):
            self.assertEqual(self.client.put(ruta, json=malo, headers=self.h_arb1).status_code, 422, malo)
        # En una fase de grupos no hay penales.
        r = self.client.put(
            ruta,
            json={"goles_local": 1, "goles_visitante": 1, "goles_penales_local": 3, "goles_penales_visitante": 2},
            headers=self.h_arb1,
        )
        self.assertEqual(r.status_code, 400)
        self.assertEqual(self.client.put("/partidos/999/marcador", json={"goles_local": 1, "goles_visitante": 0}, headers=self.h_arb1).status_code, 404)

    # ---------- cierre de acta ----------
    def test_cerrar_acta_actualiza_la_tabla(self):
        partido = self.preparar_partido("A", "B")
        final = self.terminar_partido(partido, 2, 1)
        self.assertEqual(final["estado"], "Finalizado")
        marcador = self.client.get(f"/partidos/{partido['id']}/marcador").json()
        self.assertTrue(marcador["es_resultado_final"])

        a, b = self.fila("A"), self.fila("B")
        self.assertEqual((a["partidos_jugados"], a["partidos_ganados"], a["goles_a_favor"], a["goles_en_contra"], a["diferencia_goles"], a["puntos"]), (1, 1, 2, 1, 1, 3))
        self.assertEqual((b["partidos_jugados"], b["partidos_perdidos"], b["goles_a_favor"], b["goles_en_contra"], b["diferencia_goles"], b["puntos"]), (1, 1, 1, 2, -1, 0))
        self.assertEqual(self.fila("C")["partidos_jugados"], 0)
        orden = [f["equipo_id"] for f in self.tablas()["Grupo A"]["filas"]]
        self.assertEqual(orden, [self.eq["A"]["id"], self.eq["C"]["id"], self.eq["B"]["id"]])

        # Con el acta cerrada el árbitro ya no puede modificar nada.
        ruta = f"/partidos/{partido['id']}"
        self.assertEqual(self.client.put(ruta + "/marcador", json={"goles_local": 9, "goles_visitante": 0}, headers=self.h_arb1).status_code, 409)
        self.assertEqual(self.client.post(ruta + "/cerrar", headers=self.h_arb1).status_code, 409)
        self.assertEqual(self.iniciar(partido).status_code, 409)

    def test_empate_en_fase_de_grupos_reparte_un_punto(self):
        self.jugar_partido("A", "B", 1, 1)
        for letra in "AB":
            fila = self.fila(letra)
            self.assertEqual((fila["partidos_empatados"], fila["puntos"]), (1, 1))

    def test_cerrar_exige_ser_el_arbitro_y_estar_en_juego(self):
        partido = self.preparar_partido("A", "B")
        ruta = f"/partidos/{partido['id']}/cerrar"
        self.assertEqual(self.client.post(ruta, headers=self.h_arb1).status_code, 409)  # aún Programado
        self.iniciar(partido)
        self.assertEqual(self.client.post(ruta, headers=self.h_arb2).status_code, 403)
        self.assertEqual(self.client.post(ruta, headers=self.h_ent1).status_code, 403)
        self.assertEqual(self.client.post(ruta).status_code, 401)
        self.assertEqual(self.client.post("/partidos/999/cerrar", headers=self.h_arb1).status_code, 404)

    def test_torneo_cancelado_bloquea_el_juego(self):
        partido = self.preparar_partido("A", "B")
        self.iniciar(partido)
        self.client.post(f"/torneos/{self.torneo['id']}/cancelar", headers=self.h_admin)
        ruta = f"/partidos/{partido['id']}"
        self.assertEqual(self.client.put(ruta + "/marcador", json={"goles_local": 1, "goles_visitante": 0}, headers=self.h_arb1).status_code, 409)
        self.assertEqual(self.client.post(ruta + "/cerrar", headers=self.h_arb1).status_code, 409)

    # ---------- W.O. ----------
    def test_walkover_a_favor_del_visitante(self):
        partido = self.programar_ok("A", "B")  # sin alineaciones: B se presentó y A no
        ruta = f"/partidos/{partido['id']}/walkover"
        r = self.client.post(ruta, json={"equipo_ganador_id": self.eq["B"]["id"]}, headers=self.h_admin)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["estado"], "W_O")
        marcador = self.client.get(f"/partidos/{partido['id']}/marcador").json()
        self.assertEqual((marcador["goles_local"], marcador["goles_visitante"]), (0, 3))
        self.assertTrue(marcador["es_resultado_final"])
        b, a = self.fila("B"), self.fila("A")
        self.assertEqual((b["partidos_ganados"], b["goles_a_favor"], b["puntos"]), (1, 3, 3))
        self.assertEqual((a["partidos_perdidos"], a["goles_en_contra"], a["puntos"]), (1, 3, 0))
        self.assertEqual(self.estado_fase(), "En_Juego")
        self.assertEqual(self.client.post(ruta, json={"equipo_ganador_id": self.eq["B"]["id"]}, headers=self.h_admin).status_code, 409)

    def test_walkover_a_favor_del_local(self):
        partido = self.programar_ok("A", "B")
        self.client.post(f"/partidos/{partido['id']}/walkover", json={"equipo_ganador_id": self.eq["A"]["id"]}, headers=self.h_admin)
        marcador = self.client.get(f"/partidos/{partido['id']}/marcador").json()
        self.assertEqual((marcador["goles_local"], marcador["goles_visitante"]), (3, 0))

    def test_walkover_validaciones_y_permisos(self):
        partido = self.programar_ok("A", "B")
        ruta = f"/partidos/{partido['id']}/walkover"
        cuerpo = {"equipo_ganador_id": self.eq["A"]["id"]}
        self.assertEqual(self.client.post(ruta, json=cuerpo, headers=self.h_ent1).status_code, 403)
        self.assertEqual(self.client.post(ruta, json=cuerpo, headers=self.h_arb1).status_code, 403)
        self.assertEqual(self.client.post(ruta, json=cuerpo).status_code, 401)
        self.assertEqual(self.client.post(ruta, json={"equipo_ganador_id": self.eq["C"]["id"]}, headers=self.h_admin).status_code, 400)
        self.assertEqual(self.client.post("/partidos/999/walkover", json=cuerpo, headers=self.h_admin).status_code, 404)

    def test_no_hay_walkover_en_un_partido_ya_iniciado(self):
        partido = self.preparar_partido("A", "B")
        self.iniciar(partido)
        r = self.client.post(f"/partidos/{partido['id']}/walkover", json={"equipo_ganador_id": self.eq["A"]["id"]}, headers=self.h_admin)
        self.assertEqual(r.status_code, 409)


if __name__ == "__main__":
    unittest.main()
