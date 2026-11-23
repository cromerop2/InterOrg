"""Pruebas de sanciones por fechas de suspensión."""
import unittest

from base_api import BasePartidoTest

from app.repositories.equipo_repository import EquipoRepository
from app.repositories.jugador_repository import JugadorRepository
from app.repositories.torneo_repository import TorneoRepository
from app.services.jugador_service import JugadorService


class SancionApiTest(BasePartidoTest):
    def setUp(self):
        super().setUp()
        self.a = self.ids_jugadores("A")

    def aplicar(self, id_jugador, fechas, h=None):
        return self.client.post(f"/jugadores/{id_jugador}/sanciones", json={"fechas_suspension": fechas}, headers=h or self.h_admin)

    def jugador(self, id_jugador):
        return self.client.get(f"/jugadores/{id_jugador}", headers=self.h_admin).json()

    def estado(self, id_jugador):
        j = self.jugador(id_jugador)
        return (j["sancionado"], j["fechas_suspension"])

    def planilla_sin(self, partido, letra, excluido):
        """Alineación de dos titulares, sin el jugador suspendido."""
        ids = [j for j in self.ids_jugadores(letra) if j != excluido][:2]
        cuerpo = {"jugadores": [{"jugador_id": j, "es_titular": True} for j in ids]}
        r = self.client.put(
            f"/partidos/{partido['id']}/equipos/{self.eq[letra]['id']}/alineacion", json=cuerpo, headers=self.h_dueno(letra)
        )
        self.assertEqual(r.status_code, 200, r.text)

    def elegible(self, id_jugador):
        with self.Sesion() as db:
            servicio = JugadorService(JugadorRepository(db), EquipoRepository(db), TorneoRepository(db))
            return servicio.verificar_elegibilidad(id_jugador)

    def evento(self, partido, tipo, letra, id_jugador, minuto=30):
        cuerpo = {"equipo_id": self.eq[letra]["id"], "jugador_id": id_jugador, "tipo_evento": tipo, "minuto_ocurrencia": minuto}
        return self.client.post(f"/partidos/{partido['id']}/eventos", json=cuerpo, headers=self.h_arb1)

    # ---------- aplicar ----------
    def test_aplicar_sancion(self):
        r = self.aplicar(self.a[0], 2)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertTrue(r.json()["sancionado"])
        self.assertEqual(r.json()["fechas_suspension"], 2)
        self.assertEqual(self.aplicar(self.a[0], 1).json()["fechas_suspension"], 3)  # se suman
        self.assertFalse(self.elegible(self.a[0]))

    def test_permisos_y_validaciones(self):
        self.assertEqual(self.aplicar(self.a[0], 1, h=self.h_ent1).status_code, 403)
        self.assertEqual(self.aplicar(self.a[0], 1, h=self.h_arb1).status_code, 403)
        self.assertEqual(self.client.post(f"/jugadores/{self.a[0]}/sanciones", json={"fechas_suspension": 1}).status_code, 401)
        self.assertEqual(self.aplicar(self.a[0], 0).status_code, 422)
        self.assertEqual(self.aplicar(self.a[0], 21).status_code, 422)
        self.assertEqual(self.aplicar(999, 1).status_code, 404)
        r = self.client.post(f"/jugadores/{self.a[0]}/sanciones", json={"fechas_suspension": 1, "campo_raro": 1}, headers=self.h_admin)
        self.assertEqual(r.status_code, 422)
        self.assertEqual(self.estado(self.a[0]), (False, 0))

    def test_levantar_la_sancion_borra_las_fechas(self):
        self.aplicar(self.a[0], 3)
        r = self.client.patch(f"/jugadores/{self.a[0]}/sancion", json={"sancionado": False}, headers=self.h_admin)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.estado(self.a[0]), (False, 0))

    def test_un_suspendido_no_entra_en_la_alineacion(self):
        self.aplicar(self.a[0], 1)
        partido = self.preparar_partido("A", "B", alineaciones=False)
        cuerpo = {"jugadores": [{"jugador_id": self.a[0], "es_titular": True}, {"jugador_id": self.a[1], "es_titular": True}]}
        r = self.client.put(f"/partidos/{partido['id']}/equipos/{self.eq['A']['id']}/alineacion", json=cuerpo, headers=self.h_ent1)
        self.assertEqual(r.status_code, 400)

    # ---------- cumplir las fechas ----------
    def test_cada_partido_cerrado_del_equipo_descuenta_una_fecha(self):
        self.aplicar(self.a[0], 2)
        primero = self.preparar_partido("A", "B", alineaciones=False)
        self.planilla_sin(primero, "A", self.a[0])
        self.enviar_planilla(primero, "B")
        self.terminar_partido(primero, 1, 0)
        self.assertEqual(self.estado(self.a[0]), (True, 1))

        segundo = self.preparar_partido("A", "C", alineaciones=False)
        self.planilla_sin(segundo, "A", self.a[0])
        self.enviar_planilla(segundo, "C")
        self.terminar_partido(segundo, 0, 0)
        self.assertEqual(self.estado(self.a[0]), (False, 0))  # cumplió las dos fechas
        self.assertTrue(self.elegible(self.a[0]))

    def test_los_demas_equipos_no_cumplen_la_fecha(self):
        b = self.ids_jugadores("B")
        self.aplicar(b[0], 1)
        partido = self.preparar_partido("A", "C")  # B no juega
        self.terminar_partido(partido, 1, 0)
        self.assertEqual(self.estado(b[0]), (True, 1))

    def test_la_roja_suspende_y_se_cumple_desde_el_siguiente_partido(self):
        primero = self.preparar_partido("A", "B")
        self.assertEqual(self.iniciar(primero).status_code, 200)
        self.assertEqual(self.evento(primero, "Tarjeta_Roja", "A", self.a[1]).status_code, 201)
        self.assertEqual(self.estado(self.a[1]), (True, 1))
        self.client.post(f"/partidos/{primero['id']}/cerrar", headers=self.h_arb1)
        self.assertEqual(self.estado(self.a[1]), (True, 1))  # el partido de la expulsión no cuenta

        segundo = self.preparar_partido("A", "C", alineaciones=False)
        self.planilla_sin(segundo, "A", self.a[1])
        self.enviar_planilla(segundo, "C")
        self.terminar_partido(segundo, 0, 0)
        self.assertEqual(self.estado(self.a[1]), (False, 0))

    def test_un_walkover_tambien_cuenta_como_fecha(self):
        self.aplicar(self.a[0], 1)
        partido = self.programar_ok("A", "B")
        self.client.post(f"/partidos/{partido['id']}/walkover", json={"equipo_ganador_id": self.eq["B"]["id"]}, headers=self.h_admin)
        self.assertEqual(self.estado(self.a[0]), (False, 0))

    # ---------- tarjeta roja ----------
    def test_borrar_la_roja_resta_solo_sus_fechas(self):
        partido = self.preparar_partido("A", "B")
        self.iniciar(partido)
        roja = self.evento(partido, "Tarjeta_Roja", "A", self.a[1]).json()
        self.aplicar(self.a[1], 2)  # sanción administrativa adicional
        self.assertEqual(self.estado(self.a[1]), (True, 3))
        r = self.client.delete(f"/partidos/{partido['id']}/eventos/{roja['id']}", headers=self.h_arb1)
        self.assertEqual(r.status_code, 204)
        self.assertEqual(self.estado(self.a[1]), (True, 2))  # queda la sanción del administrador


class RojaConfigurableTest(BasePartidoTest):
    REGLAS = {**BasePartidoTest.REGLAS, "fechas_por_roja": 3}

    def test_las_fechas_por_roja_se_configuran_en_el_torneo(self):
        partido = self.preparar_partido("A", "B")
        self.iniciar(partido)
        jugador = self.ids_jugadores("A")[1]
        cuerpo = {"equipo_id": self.eq["A"]["id"], "jugador_id": jugador, "tipo_evento": "Tarjeta_Roja", "minuto_ocurrencia": 50}
        self.assertEqual(self.client.post(f"/partidos/{partido['id']}/eventos", json=cuerpo, headers=self.h_arb1).status_code, 201)
        j = self.client.get(f"/jugadores/{jugador}", headers=self.h_admin).json()
        self.assertEqual((j["sancionado"], j["fechas_suspension"]), (True, 3))


if __name__ == "__main__":
    unittest.main()
