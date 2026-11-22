"""Pruebas de Grupos y Tablas de posiciones."""
import unittest

from base_api import BasePartidoTest

from app.models.fila_posicion_model import FilaPosicionModel


class TablaApiTest(BasePartidoTest):
    INICIALIZAR_GRUPOS = False  # cada prueba arma los grupos que necesita

    def ids(self, *letras):
        return [self.eq[letra]["id"] for letra in letras]

    def inicializar(self, grupos, fase=None, h=None):
        return self.client.post(
            f"/fases/{(fase or self.fase_grupos)['id']}/grupos", json={"grupos": grupos}, headers=h or self.h_admin
        )

    def grupos_normales(self):
        return {"Grupo A": self.ids("A", "B", "C"), "Grupo B": self.ids("D", "E")}

    # ---------- crear grupos ----------
    def test_inicializar_grupos(self):
        r = self.inicializar(self.grupos_normales())
        self.assertEqual(r.status_code, 201, r.text)
        tablas = r.json()
        self.assertEqual([t["nombre_grupo"] for t in tablas], ["Grupo A", "Grupo B"])
        self.assertTrue(all(not t["estado_cierre"] for t in tablas))
        self.assertEqual([f["equipo_id"] for f in tablas[0]["filas"]], self.ids("A", "B", "C"))
        for fila in tablas[0]["filas"] + tablas[1]["filas"]:
            for campo in ("partidos_jugados", "partidos_ganados", "partidos_empatados", "partidos_perdidos",
                          "goles_a_favor", "goles_en_contra", "diferencia_goles", "puntos"):
                self.assertEqual(fila[campo], 0, campo)

    def test_consulta_publica_de_las_tablas(self):
        tablas = self.inicializar(self.grupos_normales()).json()
        r = self.client.get(f"/fases/{self.fase_grupos['id']}/tablas")  # sin sesión
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), tablas)
        self.assertEqual(self.client.get(f"/tablas/{tablas[1]['id']}").json(), tablas[1])
        self.assertEqual(self.client.get("/tablas/999").status_code, 404)
        self.assertEqual(self.client.get("/fases/999/tablas").status_code, 404)

    def test_solo_el_administrador_arma_grupos(self):
        self.assertEqual(self.inicializar(self.grupos_normales(), h=self.h_ent1).status_code, 403)
        ruta = f"/fases/{self.fase_grupos['id']}/grupos"
        self.assertEqual(self.client.post(ruta, json={"grupos": self.grupos_normales()}).status_code, 401)

    def test_reglas_de_negocio(self):
        self.assertEqual(self.inicializar(self.grupos_normales(), fase={"id": 999}).status_code, 404)
        # La fase "Final" es de eliminatoria directa: no tiene grupos.
        self.assertEqual(self.inicializar(self.grupos_normales(), fase=self.fase_final).status_code, 400)
        # Equipo inexistente o sin habilitar.
        self.assertEqual(self.inicializar({"Grupo A": [self.eq["A"]["id"], 999]}).status_code, 400)
        self.assertEqual(self.inicializar({"Grupo A": [self.eq["A"]["id"], self.eq_pre["id"]]}).status_code, 400)
        # Nada de lo anterior dejó grupos creados.
        self.assertEqual(self.client.get(f"/fases/{self.fase_grupos['id']}/tablas").json(), [])
        self.assertEqual(self.inicializar(self.grupos_normales()).status_code, 201)
        self.assertEqual(self.inicializar(self.grupos_normales()).status_code, 409)  # ya tiene grupos

    def test_validaciones_de_esquema(self):
        a, b, c = self.ids("A", "B", "C")
        casos = [
            {"Grupo A": [a, b], "Grupo B": [b, c]},  # un equipo en dos grupos
            {"Grupo A": [a]},  # un solo equipo
            {"Grupo A": [a, a]},  # equipo repetido
            {},  # sin grupos
            {"  ": [a, b]},  # nombre vacío
        ]
        for caso in casos:
            self.assertEqual(self.inicializar(caso).status_code, 422, caso)
        r = self.client.post(
            f"/fases/{self.fase_grupos['id']}/grupos", json={"grupos": {"G": [a, b]}, "extra": 1}, headers=self.h_admin
        )
        self.assertEqual(r.status_code, 422)

    def test_programar_en_fase_de_grupos_exige_grupos(self):
        self.assertEqual(self.programar("A", "B").status_code, 400)  # aún no hay grupos
        self.inicializar(self.grupos_normales())
        self.assertEqual(self.programar("A", "B").status_code, 201)

    # ---------- clasificación ----------
    def poner_filas(self, valores):
        """valores: {letra: (puntos, diferencia_goles, goles_a_favor)}"""
        with self.Sesion() as db:
            for letra, (puntos, dg, gf) in valores.items():
                fila = db.query(FilaPosicionModel).filter_by(equipo_id=self.eq[letra]["id"]).one()
                fila.puntos, fila.diferencia_goles, fila.goles_a_favor = puntos, dg, gf
            db.commit()

    def orden(self, id_tabla):
        filas = self.client.get(f"/tablas/{id_tabla}").json()["filas"]
        return [f["equipo_id"] for f in filas]

    def test_orden_por_puntos_diferencia_y_goles_a_favor(self):
        tablas = self.inicializar(self.grupos_normales()).json()
        id_tabla = tablas[0]["id"]
        # Mismos puntos: gana la mayor diferencia de goles, y luego los goles a favor.
        self.poner_filas({"A": (3, 0, 2), "B": (3, 2, 4), "C": (3, 2, 5)})
        self.assertEqual(self.orden(id_tabla), self.ids("C", "B", "A"))
        # Más puntos pesa más que cualquier diferencia de goles.
        self.poner_filas({"A": (6, -5, 1), "B": (3, 9, 9), "C": (3, 2, 5)})
        self.assertEqual(self.orden(id_tabla), self.ids("A", "B", "C"))

    def test_empate_total_se_ordena_de_forma_estable(self):
        tablas = self.inicializar(self.grupos_normales()).json()
        self.poner_filas({"A": (0, 0, 0), "B": (3, 2, 4), "C": (3, 2, 4)})
        self.assertEqual(self.orden(tablas[0]["id"]), self.ids("B", "C", "A"))


if __name__ == "__main__":
    unittest.main()
