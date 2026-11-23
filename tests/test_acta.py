"""Pruebas de corrección de actas cerradas: marcador, W.O., tabla de posiciones y auditoría."""
import unittest

from base_api import BasePartidoTest

MOTIVO = "Error de digitación en el acta"


class ActaApiTest(BasePartidoTest):
    def corregir(self, partido, cuerpo, h=None):
        return self.client.patch(f"/partidos/{partido['id']}/acta", json={"motivo_auditoria": MOTIVO, **cuerpo}, headers=h or self.h_admin)

    def marcador(self, partido):
        m = self.client.get(f"/partidos/{partido['id']}/marcador").json()
        return (m["goles_local"], m["goles_visitante"])

    def auditoria(self, partido, h=None):
        return self.client.get(f"/partidos/{partido['id']}/auditoria", headers=h or self.h_admin)

    # ---------- corregir el marcador ----------
    def test_corregir_el_marcador_ajusta_la_tabla_y_deja_auditoria(self):
        partido = self.jugar_partido("A", "B", 2, 0)
        r = self.corregir(partido, {"goles_local": 1, "goles_visitante": 1})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["estado"], "Finalizado")
        self.assertEqual(self.marcador(partido), (1, 1))
        for letra in "AB":  # la victoria 2-0 se revirtió y se sumó el empate 1-1
            fila = self.fila(letra)
            self.assertEqual(
                (fila["partidos_jugados"], fila["partidos_ganados"], fila["partidos_empatados"], fila["partidos_perdidos"]),
                (1, 0, 1, 0),
            )
            self.assertEqual((fila["goles_a_favor"], fila["goles_en_contra"], fila["puntos"]), (1, 1, 1))

        registros = self.auditoria(partido).json()
        self.assertEqual(len(registros), 1)
        self.assertEqual(registros[0]["motivo"], MOTIVO)
        self.assertEqual(registros[0]["usuario_id"], self.client.get("/auth/me", headers=self.h_admin).json()["id"])
        self.assertEqual(
            registros[0]["datos_anteriores"],
            {"estado": "Finalizado", "goles_local": 2, "goles_visitante": 0, "goles_penales_local": None, "goles_penales_visitante": None},
        )
        self.assertEqual((registros[0]["datos_nuevos"]["goles_local"], registros[0]["datos_nuevos"]["goles_visitante"]), (1, 1))

    def test_cada_correccion_queda_registrada(self):
        partido = self.jugar_partido("A", "B", 2, 0)
        self.corregir(partido, {"goles_local": 1, "goles_visitante": 1})
        self.corregir(partido, {"goles_local": 0, "goles_visitante": 3})
        self.assertEqual(len(self.auditoria(partido).json()), 2)
        self.assertEqual(self.fila("B")["puntos"], 3)  # B ganó la versión final, sin acumular puntos de las anteriores
        self.assertEqual(self.fila("A")["puntos"], 0)

    # ---------- W.O. ----------
    def test_convertir_un_partido_jugado_en_walkover(self):
        partido = self.jugar_partido("A", "B", 2, 0)  # luego se prueba una alineación indebida de A
        r = self.corregir(partido, {"walkover_ganador_id": self.eq["B"]["id"]})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["estado"], "W_O")
        self.assertEqual(self.marcador(partido), (0, 3))
        a, b = self.fila("A"), self.fila("B")
        self.assertEqual((a["partidos_ganados"], a["partidos_perdidos"], a["goles_en_contra"], a["puntos"]), (0, 1, 3, 0))
        self.assertEqual((b["partidos_ganados"], b["partidos_perdidos"], b["goles_a_favor"], b["puntos"]), (1, 0, 3, 3))
        registro = self.auditoria(partido).json()[0]
        self.assertEqual((registro["datos_anteriores"]["estado"], registro["datos_nuevos"]["estado"]), ("Finalizado", "W_O"))

    def test_cambiar_el_ganador_de_un_walkover(self):
        partido = self.programar_ok("A", "B")
        self.client.post(f"/partidos/{partido['id']}/walkover", json={"equipo_ganador_id": self.eq["A"]["id"]}, headers=self.h_admin)
        r = self.corregir(partido, {"walkover_ganador_id": self.eq["B"]["id"]})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["estado"], "W_O")
        self.assertEqual(self.marcador(partido), (0, 3))
        self.assertEqual((self.fila("A")["partidos_perdidos"], self.fila("A")["puntos"]), (1, 0))
        self.assertEqual((self.fila("B")["partidos_ganados"], self.fila("B")["puntos"]), (1, 3))

    def test_un_walkover_no_se_corrige_con_marcador(self):
        partido = self.programar_ok("A", "B")
        self.client.post(f"/partidos/{partido['id']}/walkover", json={"equipo_ganador_id": self.eq["A"]["id"]}, headers=self.h_admin)
        self.assertEqual(self.corregir(partido, {"goles_local": 1, "goles_visitante": 0}).status_code, 409)

    # ---------- permisos y validaciones ----------
    def test_solo_el_administrador_corrige_y_consulta_la_auditoria(self):
        partido = self.jugar_partido("A", "B", 2, 0)
        cuerpo = {"goles_local": 1, "goles_visitante": 1}
        self.assertEqual(self.corregir(partido, cuerpo, h=self.h_arb1).status_code, 403)
        self.assertEqual(self.corregir(partido, cuerpo, h=self.h_ent1).status_code, 403)
        self.assertEqual(self.client.patch(f"/partidos/{partido['id']}/acta", json={"motivo_auditoria": MOTIVO, **cuerpo}).status_code, 401)
        self.assertEqual(self.auditoria(partido, h=self.h_ent1).status_code, 403)
        self.assertEqual(self.client.get(f"/partidos/{partido['id']}/auditoria").status_code, 401)
        self.assertEqual(self.client.get("/partidos/999/auditoria", headers=self.h_admin).status_code, 404)
        self.assertEqual(self.marcador(partido), (2, 0))  # nada cambió

    def test_validaciones_del_cuerpo(self):
        partido = self.jugar_partido("A", "B", 2, 0)
        ruta = f"/partidos/{partido['id']}/acta"
        ganador = self.eq["B"]["id"]
        casos = [
            {"goles_local": 1, "goles_visitante": 1},  # sin motivo
            {"motivo_auditoria": "corto", "goles_local": 1, "goles_visitante": 1},
            {"motivo_auditoria": MOTIVO},  # ni marcador ni W.O.
            {"motivo_auditoria": MOTIVO, "goles_local": 1, "goles_visitante": 1, "walkover_ganador_id": ganador},
            {"motivo_auditoria": MOTIVO, "goles_local": 1},
            {"motivo_auditoria": MOTIVO, "goles_local": 1, "goles_visitante": 1, "goles_penales_local": 3},
            {"motivo_auditoria": MOTIVO, "walkover_ganador_id": ganador, "goles_penales_local": 1, "goles_penales_visitante": 0},
            {"motivo_auditoria": MOTIVO, "goles_local": -1, "goles_visitante": 0},
            {"motivo_auditoria": MOTIVO, "goles_local": 1, "goles_visitante": 0, "campo_raro": 1},
        ]
        for caso in casos:
            self.assertEqual(self.client.patch(ruta, json=caso, headers=self.h_admin).status_code, 422, caso)

    def test_solo_se_corrigen_actas_cerradas_y_datos_coherentes(self):
        programado = self.programar_ok("A", "B")
        self.assertEqual(self.corregir(programado, {"goles_local": 1, "goles_visitante": 0}).status_code, 409)
        en_juego = self.preparar_partido("D", "E")
        self.iniciar(en_juego)
        self.assertEqual(self.corregir(en_juego, {"goles_local": 1, "goles_visitante": 0}).status_code, 409)
        self.assertEqual(self.corregir({"id": 999}, {"goles_local": 1, "goles_visitante": 0}).status_code, 404)

        jugado = self.jugar_partido("A", "C", 1, 0)
        self.assertEqual(self.corregir(jugado, {"walkover_ganador_id": self.eq["B"]["id"]}).status_code, 400)  # B no juega ese partido
        penales = {"goles_local": 1, "goles_visitante": 1, "goles_penales_local": 3, "goles_penales_visitante": 2}
        self.assertEqual(self.corregir(jugado, penales).status_code, 400)  # no hay penales en fase de grupos
        self.assertEqual(self.marcador(jugado), (1, 0))

    # ---------- grupo cerrado, fase finalizada, torneo cancelado ----------
    def test_un_grupo_cerrado_hay_que_reabrirlo(self):
        ab = self.jugar_partido("A", "B", 2, 0)
        self.jugar_partido("A", "C", 1, 0)
        self.jugar_partido("B", "C", 1, 0)
        self.assertEqual(self.cerrar_grupo("Grupo A").status_code, 200)
        r = self.corregir(ab, {"goles_local": 0, "goles_visitante": 1})
        self.assertEqual(r.status_code, 409)
        self.assertIn("reábrelo", r.json()["detail"])

        ruta = f"/tablas/{self.tablas()['Grupo A']['id']}/reabrir"
        self.assertEqual(self.client.post(ruta, headers=self.h_ent1).status_code, 403)
        self.assertEqual(self.client.post(ruta).status_code, 401)
        r = self.client.post(ruta, headers=self.h_admin)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertFalse(r.json()["estado_cierre"])
        self.assertEqual(self.client.post(ruta, headers=self.h_admin).status_code, 409)  # ya está abierto
        self.assertEqual(self.client.post("/tablas/999/reabrir", headers=self.h_admin).status_code, 404)
        self.assertEqual(self.corregir(ab, {"goles_local": 0, "goles_visitante": 1}).status_code, 200)

    def test_una_fase_finalizada_no_se_toca(self):
        partidos = self.jugar_toda_la_fase_de_grupos()
        self.cerrar_fase_de_grupos()
        self.assertEqual(self.corregir(partidos[0], {"goles_local": 0, "goles_visitante": 1}).status_code, 409)
        ruta = f"/tablas/{self.tablas()['Grupo A']['id']}/reabrir"
        self.assertEqual(self.client.post(ruta, headers=self.h_admin).status_code, 409)

    def test_torneo_cancelado_no_admite_correcciones(self):
        partido = self.jugar_partido("A", "B", 2, 0)
        self.client.post(f"/torneos/{self.torneo['id']}/cancelar", headers=self.h_admin)
        self.assertEqual(self.corregir(partido, {"goles_local": 1, "goles_visitante": 1}).status_code, 409)

    # ---------- eliminatoria ----------
    def test_corregir_penales_cambia_al_clasificado(self):
        self.jugar_toda_la_fase_de_grupos()
        self.cerrar_fase_de_grupos()
        final = self.preparar_partido("A", "B", fase=self.fase_final)
        self.terminar_partido(final, 1, 1, penales=(4, 3))
        clasificados = lambda: self.client.get(f"/fases/{self.fase_final['id']}/clasificados").json()["clasificados"]
        self.assertEqual(clasificados(), [self.eq["A"]["id"]])

        r = self.corregir(final, {"goles_local": 1, "goles_visitante": 1, "goles_penales_local": 3, "goles_penales_visitante": 4})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(clasificados(), [self.eq["B"]["id"]])

        # Si el marcador deja de estar empatado, los penales se descartan.
        self.assertEqual(self.corregir(final, {"goles_local": 2, "goles_visitante": 1}).status_code, 200)
        guardado = self.client.get(f"/partidos/{final['id']}/marcador").json()
        self.assertEqual((guardado["goles_penales_local"], guardado["goles_penales_visitante"]), (None, None))
        self.assertEqual(clasificados(), [self.eq["A"]["id"]])

        # Un empate exige penales con ganador.
        self.assertEqual(self.corregir(final, {"goles_local": 2, "goles_visitante": 2}).status_code, 400)
        igualados = {"goles_local": 1, "goles_visitante": 1, "goles_penales_local": 3, "goles_penales_visitante": 3}
        self.assertEqual(self.corregir(final, igualados).status_code, 400)

    # ---------- efecto sobre los goleadores ----------
    def test_un_walkover_deja_de_contar_los_goles(self):
        partido = self.preparar_partido("A", "B")
        self.iniciar(partido)
        gol = {"equipo_id": self.eq["A"]["id"], "jugador_id": self.ids_jugadores("A")[0], "tipo_evento": "Gol", "minuto_ocurrencia": 10}
        self.assertEqual(self.client.post(f"/partidos/{partido['id']}/eventos", json=gol, headers=self.h_arb1).status_code, 201)
        self.client.post(f"/partidos/{partido['id']}/cerrar", headers=self.h_arb1)
        ruta = f"/torneos/{self.torneo['id']}/goleadores"
        self.assertEqual(len(self.client.get(ruta).json()), 1)
        self.corregir(partido, {"walkover_ganador_id": self.eq["B"]["id"]})
        self.assertEqual(self.client.get(ruta).json(), [])


if __name__ == "__main__":
    unittest.main()
