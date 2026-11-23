"""Pruebas de Eventos de partido: validaciones contra la alineación, efectos, correcciones y goleadores."""
import unittest

from base_api import BasePartidoTest


class EventoApiTest(BasePartidoTest):
    """Partido A-B ya iniciado. Titulares: a[0] y a[1] / b[0] y b[1]. Suplentes: a[2] / b[2]."""

    def setUp(self):
        super().setUp()
        self.partido = self.preparar_partido("A", "B")
        self.assertEqual(self.iniciar(self.partido).status_code, 200)
        self.a = self.ids_jugadores("A")
        self.b = self.ids_jugadores("B")
        self.ruta = f"/partidos/{self.partido['id']}/eventos"

    def ev(self, tipo, letra, jugador, minuto=10, secundario=None, h=None, partido=None, **extra):
        cuerpo = {
            "equipo_id": self.eq[letra]["id"],
            "jugador_id": jugador,
            "tipo_evento": tipo,
            "minuto_ocurrencia": minuto,
            **extra,
        }
        if secundario is not None:
            cuerpo["jugador_secundario_id"] = secundario
        ruta = f"/partidos/{(partido or self.partido)['id']}/eventos"
        return self.client.post(ruta, json=cuerpo, headers=h or self.h_arb1)

    def ev_ok(self, *args, **kwargs):
        r = self.ev(*args, **kwargs)
        self.assertEqual(r.status_code, 201, r.text)
        return r.json()

    def marcador(self):
        m = self.client.get(f"/partidos/{self.partido['id']}/marcador").json()
        return (m["goles_local"], m["goles_visitante"])

    def sancionado(self, id_jugador):
        return self.client.get(f"/jugadores/{id_jugador}", headers=self.h_admin).json()["sancionado"]

    # ---------- efectos sobre el marcador ----------
    def test_goles_y_autogoles_mueven_el_marcador(self):
        self.ev_ok("Gol", "A", self.a[0], minuto=30)
        self.assertEqual(self.marcador(), (1, 0))
        self.ev_ok("Gol", "B", self.b[0], minuto=5)
        self.assertEqual(self.marcador(), (1, 1))
        self.ev_ok("Autogol", "A", self.a[1], minuto=40)  # lo anota el rival
        self.assertEqual(self.marcador(), (1, 2))
        # El minuto a minuto es público y va ordenado por minuto.
        eventos = self.client.get(self.ruta).json()
        self.assertEqual([e["minuto_ocurrencia"] for e in eventos], [5, 30, 40])
        self.assertEqual(self.client.get("/partidos/999/eventos").status_code, 404)

    def test_asistencia_y_tarjeta_amarilla_no_mueven_el_marcador(self):
        self.ev_ok("Asistencia", "A", self.a[1], minuto=11)
        self.ev_ok("Tarjeta_Amarilla", "B", self.b[0], minuto=20, comentarios="Falta táctica")
        self.assertEqual(self.marcador(), (0, 0))
        self.assertEqual(self.client.get(self.ruta).json()[1]["comentarios"], "Falta táctica")

    # ---------- permisos y estado ----------
    def test_solo_el_arbitro_designado_registra(self):
        self.assertEqual(self.ev("Gol", "A", self.a[0], h=self.h_arb2).status_code, 403)
        self.assertEqual(self.ev("Gol", "A", self.a[0], h=self.h_admin).status_code, 403)
        self.assertEqual(self.ev("Gol", "A", self.a[0], h=self.h_ent1).status_code, 403)
        cuerpo = {"equipo_id": self.eq["A"]["id"], "jugador_id": self.a[0], "tipo_evento": "Gol", "minuto_ocurrencia": 1}
        self.assertEqual(self.client.post(self.ruta, json=cuerpo).status_code, 401)
        self.assertEqual(self.marcador(), (0, 0))

    def test_el_partido_debe_estar_en_juego(self):
        otro = self.preparar_partido("D", "E")  # Programado, no iniciado
        r = self.ev("Gol", "D", self.ids_jugadores("D")[0], partido=otro)
        self.assertEqual(r.status_code, 409)
        self.assertEqual(self.ev("Gol", "A", self.a[0], partido={"id": 999}).status_code, 404)

    # ---------- validación contra la alineación ----------
    def test_el_jugador_debe_estar_en_la_alineacion(self):
        ajeno = self.ids_jugadores("C")[0]
        self.assertEqual(self.ev("Gol", "A", ajeno).status_code, 400)  # jugador de otro equipo
        self.assertEqual(self.ev("Gol", "C", ajeno).status_code, 400)  # equipo que no juega
        self.assertEqual(self.ev("Gol", "A", self.b[0]).status_code, 400)  # jugador del rival
        self.assertEqual(self.marcador(), (0, 0))

    def test_el_suplente_no_marca_pero_puede_recibir_tarjeta(self):
        self.assertEqual(self.ev("Gol", "A", self.a[2]).status_code, 400)  # está en el banco
        self.assertEqual(self.ev("Tarjeta_Amarilla", "A", self.a[2]).status_code, 201)

    def test_asistente_del_gol(self):
        self.ev_ok("Gol", "A", self.a[0], secundario=self.a[1])
        self.assertEqual(self.marcador(), (1, 0))
        self.assertEqual(self.ev("Gol", "A", self.a[0], secundario=self.a[2]).status_code, 400)  # asistente en el banco
        self.assertEqual(self.ev("Gol", "A", self.a[0], secundario=self.b[0]).status_code, 400)  # asistente rival
        self.assertEqual(self.ev("Gol", "A", self.a[0], secundario=self.a[0]).status_code, 422)  # el mismo jugador
        self.assertEqual(self.ev("Tarjeta_Amarilla", "A", self.a[0], secundario=self.a[1]).status_code, 422)
        self.assertEqual(self.marcador(), (1, 0))

    # ---------- sustituciones ----------
    def test_sustitucion(self):
        # Sin jugador que sale: 422. Quien sale debe estar en cancha; quien entra, ser suplente.
        self.assertEqual(self.ev("Sustitucion", "A", self.a[2]).status_code, 422)
        self.assertEqual(self.ev("Sustitucion", "A", self.a[2], secundario=self.ids_jugadores("C")[0]).status_code, 400)
        self.assertEqual(self.ev("Sustitucion", "A", self.a[1], secundario=self.a[0]).status_code, 400)  # entra un titular

        self.ev_ok("Sustitucion", "A", self.a[2], minuto=60, secundario=self.a[0])
        self.assertEqual(self.ev("Gol", "A", self.a[0]).status_code, 400)  # el que salió ya no juega
        self.ev_ok("Gol", "A", self.a[2], minuto=70)  # el que entró sí
        self.assertEqual(self.marcador(), (1, 0))

    def test_maximo_de_sustituciones(self):
        self.ev_ok("Sustitucion", "A", self.a[2], secundario=self.a[0])
        r = self.ev("Sustitucion", "A", self.a[2], secundario=self.a[1])  # el reglamento de prueba permite 1
        self.assertEqual(r.status_code, 409)

    # ---------- tarjeta roja ----------
    def test_tarjeta_roja_expulsa_y_sanciona(self):
        self.assertFalse(self.sancionado(self.a[1]))
        self.ev_ok("Tarjeta_Roja", "A", self.a[1], minuto=40, comentarios="Conducta violenta")
        self.assertTrue(self.sancionado(self.a[1]))  # suspensión automática hasta que el administrador la levante
        self.assertEqual(self.ev("Gol", "A", self.a[1]).status_code, 400)  # ya no está en el campo
        self.assertEqual(self.ev("Tarjeta_Amarilla", "A", self.a[1]).status_code, 400)  # ya expulsado
        self.assertEqual(self.ev("Sustitucion", "A", self.a[2], secundario=self.a[1]).status_code, 400)

    # ---------- corregir errores ----------
    def test_eliminar_evento_revierte_el_marcador(self):
        gol = self.ev_ok("Gol", "A", self.a[0])
        autogol = self.ev_ok("Autogol", "A", self.a[1])
        self.assertEqual(self.marcador(), (1, 1))
        borrar = lambda e, h=None: self.client.delete(f"{self.ruta}/{e['id']}", headers=h or self.h_arb1)
        self.assertEqual(borrar(gol, self.h_arb2).status_code, 403)
        self.assertEqual(borrar(gol, self.h_admin).status_code, 403)
        self.assertEqual(borrar(gol).status_code, 204)
        self.assertEqual(self.marcador(), (0, 1))
        self.assertEqual(borrar(autogol).status_code, 204)
        self.assertEqual(self.marcador(), (0, 0))
        self.assertEqual(borrar(gol).status_code, 404)  # ya no existe

    def test_eliminar_tarjeta_roja_levanta_la_sancion(self):
        roja = self.ev_ok("Tarjeta_Roja", "A", self.a[1])
        self.assertTrue(self.sancionado(self.a[1]))
        self.assertEqual(self.client.delete(f"{self.ruta}/{roja['id']}", headers=self.h_arb1).status_code, 204)
        self.assertFalse(self.sancionado(self.a[1]))
        self.ev_ok("Gol", "A", self.a[1])  # vuelve a poder jugar

    def test_no_se_toca_un_evento_de_otro_partido_ni_con_el_acta_cerrada(self):
        gol = self.ev_ok("Gol", "A", self.a[0])
        otro = self.preparar_partido("D", "E")
        self.iniciar(otro)
        self.assertEqual(self.client.delete(f"/partidos/{otro['id']}/eventos/{gol['id']}", headers=self.h_arb1).status_code, 404)
        self.client.post(f"/partidos/{self.partido['id']}/cerrar", headers=self.h_arb1)
        self.assertEqual(self.client.delete(f"{self.ruta}/{gol['id']}", headers=self.h_arb1).status_code, 409)
        self.assertEqual(self.ev("Gol", "A", self.a[0]).status_code, 409)

    # ---------- esquema ----------
    def test_validaciones_de_esquema(self):
        base = {"equipo_id": self.eq["A"]["id"], "jugador_id": self.a[0], "tipo_evento": "Gol", "minuto_ocurrencia": 10}
        for cambio in (
            {"minuto_ocurrencia": 200},
            {"minuto_ocurrencia": -1},
            {"tipo_evento": "Penal"},
            {"comentarios": "  "},
            {"campo_raro": 1},
        ):
            r = self.client.post(self.ruta, json={**base, **cambio}, headers=self.h_arb1)
            self.assertEqual(r.status_code, 422, cambio)

    # ---------- goleadores ----------
    def test_goleadores_cuentan_solo_partidos_finalizados(self):
        self.ev_ok("Gol", "A", self.a[0], minuto=10)
        self.ev_ok("Gol", "A", self.a[0], minuto=20)
        self.ev_ok("Gol", "B", self.b[0], minuto=30)
        self.ev_ok("Autogol", "A", self.a[1], minuto=40)  # no suma al goleador
        ruta = f"/torneos/{self.torneo['id']}/goleadores"
        self.assertEqual(self.client.get(ruta).json(), [])  # el acta sigue abierta

        self.assertEqual(self.client.post(f"/partidos/{self.partido['id']}/cerrar", headers=self.h_arb1).status_code, 200)
        goleadores = self.client.get(ruta).json()  # público
        self.assertEqual([(g["jugador_id"], g["goles"]) for g in goleadores], [(self.a[0], 2), (self.b[0], 1)])
        self.assertEqual(goleadores[0]["equipo_id"], self.eq["A"]["id"])
        self.assertTrue(goleadores[0]["nombre_completo"])
        self.assertEqual(len(self.client.get(ruta + "?limite=1").json()), 1)
        self.assertEqual(self.client.get("/torneos/999/goleadores").status_code, 404)
        self.assertEqual(self.client.get(ruta + "?limite=0").status_code, 422)


if __name__ == "__main__":
    unittest.main()
