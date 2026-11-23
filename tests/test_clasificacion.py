"""Pruebas de clasificación: desempate directo, cierre de grupos y fases, clasificados y estadísticas."""
import unittest

from base_api import BasePartidoTest
from fastapi import HTTPException

from app.repositories.fila_posicion_repository import FilaPosicionRepository
from app.services.fila_posicion_service import FilaPosicionService


class ClasificacionApiTest(BasePartidoTest):
    def ids(self, *letras):
        return [self.eq[letra]["id"] for letra in letras]

    def orden(self, grupo="Grupo A"):
        return [f["equipo_id"] for f in self.tablas()[grupo]["filas"]]

    def cerrar_grupo(self, grupo, h=None):
        return self.client.post(f"/tablas/{self.tablas()[grupo]['id']}/cerrar", headers=h or self.h_admin)

    def jugar_toda_la_fase_de_grupos(self):
        """A gana sus dos partidos, B le gana a C, y D empata con E."""
        self.jugar_partido("A", "B", 2, 0)
        self.jugar_partido("A", "C", 1, 0)
        self.jugar_partido("B", "C", 1, 0)
        self.jugar_partido("D", "E", 1, 1)

    def cerrar_fase_de_grupos(self):
        for grupo in ("Grupo A", "Grupo B"):
            self.assertEqual(self.cerrar_grupo(grupo).status_code, 200)
        r = self.client.post(f"/fases/{self.fase_grupos['id']}/cerrar", headers=self.h_admin)
        self.assertEqual(r.status_code, 200, r.text)

    # ---------- desempate ----------
    def test_desempate_por_enfrentamiento_directo(self):
        # A y B quedan igualados en puntos, diferencia y goles a favor, pero B le ganó a A.
        self.jugar_partido("B", "A", 1, 0)
        self.jugar_partido("A", "C", 2, 1)
        self.jugar_partido("C", "B", 2, 1)
        a, b, c = self.fila("A"), self.fila("B"), self.fila("C")
        self.assertEqual((a["puntos"], a["diferencia_goles"], a["goles_a_favor"]), (3, 0, 2))
        self.assertEqual((b["puntos"], b["diferencia_goles"], b["goles_a_favor"]), (3, 0, 2))
        self.assertEqual(c["goles_a_favor"], 3)
        # C va primero por goles a favor; B supera a A por el resultado entre ambos.
        self.assertEqual(self.orden(), self.ids("C", "B", "A"))

    # ---------- cierre de grupo ----------
    def test_cerrar_grupo_exige_todos_los_partidos(self):
        self.jugar_partido("A", "B", 2, 0)
        r = self.cerrar_grupo("Grupo A")
        self.assertEqual(r.status_code, 409)
        self.assertIn("Faltan", r.json()["detail"])
        self.jugar_partido("A", "C", 1, 0)
        pendiente = self.preparar_partido("B", "C")  # programado, sin jugar
        r = self.cerrar_grupo("Grupo A")
        self.assertEqual(r.status_code, 409)
        self.assertIn("sin finalizar", r.json()["detail"])
        self.terminar_partido(pendiente, 1, 0)

        r = self.cerrar_grupo("Grupo A")
        self.assertEqual(r.status_code, 200, r.text)
        self.assertTrue(r.json()["estado_cierre"])
        self.assertEqual(r.json()["clasificados"], self.ids("A", "B"))  # pasan 2 por grupo
        self.assertEqual([f["equipo_id"] for f in r.json()["filas"]], self.ids("A", "B", "C"))
        self.assertEqual(self.cerrar_grupo("Grupo A").status_code, 409)  # ya cerrado

    def test_cerrar_grupo_permisos_y_existencia(self):
        self.jugar_partido("D", "E", 3, 1)
        self.assertEqual(self.cerrar_grupo("Grupo B", h=self.h_ent2).status_code, 403)
        self.assertEqual(self.cerrar_grupo("Grupo B", h=self.h_arb1).status_code, 403)
        ruta = f"/tablas/{self.tablas()['Grupo B']['id']}/cerrar"
        self.assertEqual(self.client.post(ruta).status_code, 401)
        self.assertEqual(self.client.post("/tablas/999/cerrar", headers=self.h_admin).status_code, 404)
        r = self.cerrar_grupo("Grupo B")
        self.assertEqual(r.json()["clasificados"], self.ids("D", "E"))

    # ---------- clasificados y cierre de fase ----------
    def test_clasificados_de_la_fase_de_grupos(self):
        ruta = f"/fases/{self.fase_grupos['id']}/clasificados"
        self.assertEqual(self.client.get(ruta).status_code, 409)  # los grupos siguen abiertos
        self.jugar_toda_la_fase_de_grupos()
        self.assertEqual(self.client.get(ruta).status_code, 409)  # jugados, pero sin cerrar
        self.cerrar_fase_de_grupos()
        r = self.client.get(ruta)  # público
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {"fase_id": self.fase_grupos["id"], "clasificados": self.ids("A", "B", "D", "E")})
        self.assertEqual(self.client.get("/fases/999/clasificados").status_code, 404)

    def test_cerrar_fase(self):
        ruta = f"/fases/{self.fase_grupos['id']}/cerrar"
        self.assertEqual(self.client.post(ruta, headers=self.h_admin).status_code, 409)  # sin partidos
        self.jugar_toda_la_fase_de_grupos()
        self.assertEqual(self.client.post(ruta, headers=self.h_admin).status_code, 409)  # grupos abiertos
        self.assertEqual(self.cerrar_grupo("Grupo A").status_code, 200)
        self.assertEqual(self.client.post(ruta, headers=self.h_admin).status_code, 409)  # falta el Grupo B
        self.assertEqual(self.cerrar_grupo("Grupo B").status_code, 200)

        self.assertEqual(self.client.post(ruta, headers=self.h_ent1).status_code, 403)
        self.assertEqual(self.client.post(ruta).status_code, 401)
        r = self.client.post(ruta, headers=self.h_admin)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["estado"], "Finalizada")
        self.assertEqual(self.client.post(ruta, headers=self.h_admin).status_code, 409)
        self.assertEqual(self.client.post("/fases/999/cerrar", headers=self.h_admin).status_code, 404)

    def test_una_fase_finalizada_no_admite_mas_partidos(self):
        self.jugar_toda_la_fase_de_grupos()
        self.cerrar_fase_de_grupos()
        self.assertEqual(self.programar("C", "A", hora="2026-12-18T10:00:00").status_code, 409)

    # ---------- eliminatoria directa ----------
    def test_final_definida_por_penales_y_cierre_del_torneo(self):
        self.jugar_toda_la_fase_de_grupos()
        self.cerrar_fase_de_grupos()

        final = self.preparar_partido("A", "B", fase=self.fase_final)
        self.assertEqual(self.iniciar(final).status_code, 200)
        marcador = f"/partidos/{final['id']}/marcador"
        cerrar = f"/partidos/{final['id']}/cerrar"
        empate = {"goles_local": 1, "goles_visitante": 1}

        self.client.put(marcador, json=empate, headers=self.h_arb1)
        self.assertEqual(self.client.post(cerrar, headers=self.h_arb1).status_code, 409)  # empate sin penales
        self.client.put(marcador, json={**empate, "goles_penales_local": 3, "goles_penales_visitante": 3}, headers=self.h_arb1)
        self.assertEqual(self.client.post(cerrar, headers=self.h_arb1).status_code, 409)  # penales empatados
        r = self.client.put(marcador, json={**empate, "goles_penales_local": 4, "goles_penales_visitante": 3}, headers=self.h_arb1)
        self.assertEqual(r.status_code, 200, r.text)
        r = self.client.post(cerrar, headers=self.h_arb1)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["estado"], "Finalizado")
        guardado = self.client.get(marcador).json()
        self.assertEqual((guardado["goles_penales_local"], guardado["goles_penales_visitante"]), (4, 3))

        # Una eliminatoria no usa tabla de posiciones: no cambia la de los grupos.
        self.assertEqual(self.fila("A")["partidos_jugados"], 2)
        r = self.client.get(f"/fases/{self.fase_final['id']}/clasificados")
        self.assertEqual(r.json()["clasificados"], self.ids("A"))  # ganó por penales

        r = self.client.post(f"/fases/{self.fase_final['id']}/cerrar", headers=self.h_admin)
        self.assertEqual(r.status_code, 200, r.text)
        r = self.client.post(f"/torneos/{self.torneo['id']}/finalizar", headers=self.h_admin)
        self.assertEqual(r.json()["estado"], "Finalizado")
        # Con el torneo finalizado ya no se programa nada.
        self.assertEqual(self.programar("C", "D", fase=self.fase_final, hora="2026-12-19T10:00:00").status_code, 409)

    def test_eliminatoria_sin_partidos_no_tiene_clasificados(self):
        self.assertEqual(self.client.get(f"/fases/{self.fase_final['id']}/clasificados").status_code, 409)

    # ---------- estadísticas del equipo ----------
    def test_estadisticas_del_equipo(self):
        self.jugar_partido("A", "B", 2, 0)
        ruta = f"/equipos/{self.eq['A']['id']}/estadisticas"
        r = self.client.get(ruta, headers=self.h_ent1)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()), 1)  # una fila por grupo en el que juega
        self.assertEqual((r.json()[0]["puntos"], r.json()[0]["goles_a_favor"]), (3, 2))
        self.assertEqual(self.client.get(ruta, headers=self.h_admin).status_code, 200)
        self.assertEqual(self.client.get(ruta, headers=self.h_ent2).status_code, 403)
        self.assertEqual(self.client.get(ruta).status_code, 401)
        self.assertEqual(self.client.get("/equipos/999/estadisticas", headers=self.h_admin).status_code, 404)
        # F no está en ningún grupo.
        r = self.client.get(f"/equipos/{self.eq['F']['id']}/estadisticas", headers=self.h_ent2)
        self.assertEqual(r.json(), [])

    # ---------- procesar y revertir resultados ----------
    def test_revertir_resultado_deja_la_tabla_como_estaba(self):
        id_tabla = self.tablas()["Grupo A"]["id"]
        id_equipo = self.eq["A"]["id"]
        with self.Sesion() as db:
            servicio = FilaPosicionService(FilaPosicionRepository(db))
            servicio.procesar_resultado_partido(id_tabla, id_equipo, 3, 1)  # victoria
            servicio.procesar_resultado_partido(id_tabla, id_equipo, 1, 1)  # empate
            fila = servicio.procesar_resultado_partido(id_tabla, id_equipo, 0, 2)  # derrota
            self.assertEqual(
                (fila.partidos_jugados, fila.partidos_ganados, fila.partidos_empatados, fila.partidos_perdidos),
                (3, 1, 1, 1),
            )
            self.assertEqual((fila.goles_a_favor, fila.goles_en_contra, fila.diferencia_goles, fila.puntos), (4, 4, 0, 4))

            servicio.revertir_resultado_partido(id_tabla, id_equipo, 0, 2)
            servicio.revertir_resultado_partido(id_tabla, id_equipo, 1, 1)
            fila = servicio.revertir_resultado_partido(id_tabla, id_equipo, 3, 1)
            for campo in ("partidos_jugados", "partidos_ganados", "partidos_empatados", "partidos_perdidos",
                          "goles_a_favor", "goles_en_contra", "diferencia_goles", "puntos"):
                self.assertEqual(getattr(fila, campo), 0, campo)

    def test_los_puntos_son_configurables(self):
        id_tabla = self.tablas()["Grupo A"]["id"]
        with self.Sesion() as db:
            servicio = FilaPosicionService(FilaPosicionRepository(db))
            fila = servicio.procesar_resultado_partido(id_tabla, self.eq["A"]["id"], 2, 0, puntos_victoria=2)
            self.assertEqual(fila.puntos, 2)
            fila = servicio.procesar_resultado_partido(id_tabla, self.eq["A"]["id"], 1, 1, puntos_empate=0)
            self.assertEqual(fila.puntos, 2)

    def test_procesar_un_equipo_que_no_esta_en_la_tabla(self):
        id_tabla = self.tablas()["Grupo A"]["id"]
        with self.Sesion() as db:
            servicio = FilaPosicionService(FilaPosicionRepository(db))
            with self.assertRaises(HTTPException) as contexto:
                servicio.procesar_resultado_partido(id_tabla, self.eq["D"]["id"], 1, 0)
            self.assertEqual(contexto.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
