"""Pruebas de la entidad Fase: ciclo de estados, orden y consulta pública."""
import unittest

from base_api import BasePartidoTest


class FaseApiTest(BasePartidoTest):
    def estado(self, fase):
        return self.client.get(f"/fases/{fase['id']}").json()["estado"]

    def test_ciclo_de_estados_programada_en_juego_finalizada(self):
        self.assertEqual(self.estado(self.fase_grupos), "Programada")
        partido = self.preparar_partido("A", "B")
        self.assertEqual(self.estado(self.fase_grupos), "Programada")  # programar no inicia la fase
        self.terminar_partido(partido, 1, 0)
        self.assertEqual(self.estado(self.fase_grupos), "En_Juego")
        self.assertEqual(self.estado(self.fase_final), "Programada")  # la otra fase no cambia

    def test_las_fases_se_listan_en_el_orden_de_creacion(self):
        r = self.client.get(f"/torneos/{self.torneo['id']}/fases")
        self.assertEqual([f["nombre"] for f in r.json()], ["Fase de Grupos", "Final"])
        self.assertEqual([f["tipo_formato"] for f in r.json()], ["Grupos", "Eliminatoria_Directa"])

    def test_no_se_programa_la_final_antes_de_cerrar_los_grupos(self):
        r = self.programar("A", "B", fase=self.fase_final)
        self.assertEqual(r.status_code, 409)

    def test_cerrar_fase_deja_programar_la_siguiente(self):
        self.jugar_toda_la_fase_de_grupos()
        self.cerrar_fase_de_grupos()
        self.assertEqual(self.estado(self.fase_grupos), "Finalizada")
        r = self.programar("A", "D", fase=self.fase_final, hora="2026-12-15T10:00:00")
        self.assertEqual(r.status_code, 201, r.text)

    def test_fases_ya_no_se_crean_con_el_torneo_en_curso(self):
        r = self.client.post(
            f"/torneos/{self.torneo['id']}/fases", json={"nombre": "Extra", "tipo_formato": "Grupos"}, headers=self.h_admin
        )
        self.assertEqual(r.status_code, 409)


if __name__ == "__main__":
    unittest.main()
