"""Pruebas de programación automática: cruces, horarios, árbitros y fases de eliminatoria."""
import unittest
from datetime import datetime, timedelta

from base_api import BasePartidoTest

from app.services.fixture_service import rondas_todos_contra_todos


def hay_cruce(partidos, minutos=90):
    """True si dos partidos comparten cancha, equipo o árbitro con menos de `minutos` de diferencia."""
    ventana = timedelta(minutes=minutos)
    for i, p in enumerate(partidos):
        for q in partidos[i + 1:]:
            if abs(datetime.fromisoformat(p["fecha_hora"]) - datetime.fromisoformat(q["fecha_hora"])) >= ventana:
                continue
            equipos = {p["equipo_local_id"], p["equipo_visitante_id"]} & {q["equipo_local_id"], q["equipo_visitante_id"]}
            if p["cancha_id"] == q["cancha_id"] or equipos or (p["arbitro_id"] and p["arbitro_id"] == q["arbitro_id"]):
                return True
    return False


class RondasTest(unittest.TestCase):
    def test_todos_contra_todos(self):
        for n in (2, 3, 4, 5, 6):
            rondas = rondas_todos_contra_todos(list(range(1, n + 1)))
            pares = [frozenset(cruce) for ronda in rondas for cruce in ronda]
            self.assertEqual(len(pares), n * (n - 1) // 2, n)  # todas las parejas
            self.assertEqual(len(set(pares)), len(pares), n)  # ninguna repetida
            for ronda in rondas:  # en una ronda nadie juega dos veces
                jugando = [equipo for cruce in ronda for equipo in cruce]
                self.assertEqual(len(jugando), len(set(jugando)), n)


class FixtureApiTest(BasePartidoTest):
    def fixture(self, cuerpo=None, fase=None, h=None):
        ruta = f"/fases/{(fase or self.fase_grupos)['id']}/fixture"
        return self.client.post(ruta, json=cuerpo, headers=h or self.h_admin)

    def fixture_ok(self, cuerpo=None, **kwargs):
        r = self.fixture(cuerpo, **kwargs)
        self.assertEqual(r.status_code, 201, r.text)
        return r.json()

    def parejas(self, partidos):
        return {frozenset((p["equipo_local_id"], p["equipo_visitante_id"])) for p in partidos}

    # ---------- fase de grupos ----------
    def test_genera_todos_los_cruces_de_cada_grupo(self):
        partidos = self.fixture_ok()
        self.assertEqual(len(partidos), 4)  # 3 en el Grupo A y 1 en el Grupo B
        esperadas = {frozenset(self.ids_de(*par)) for par in ("AB", "AC", "BC", "DE")}
        self.assertEqual(self.parejas(partidos), esperadas)
        self.assertTrue(all(p["estado"] == "Programado" for p in partidos))
        self.assertTrue(all("2026-12-01" <= p["fecha_hora"][:10] <= "2026-12-20" for p in partidos))
        self.assertFalse(hay_cruce(partidos))
        for p in partidos:  # cada partido nace con su marcador
            self.assertEqual(self.client.get(f"/partidos/{p['id']}/marcador").status_code, 200)
        listado = self.client.get(f"/fases/{self.fase_grupos['id']}/partidos").json()
        self.assertEqual(len(listado), 4)

    def ids_de(self, *letras):
        return [self.eq[letra]["id"] for letra in letras]

    def test_un_solo_horario_por_dia(self):
        cuerpo = {"horas": ["09:00"], "canchas": [self.cancha1["id"]], "fecha_inicio": "2026-12-10"}
        partidos = self.fixture_ok(cuerpo)
        self.assertEqual(sorted(p["fecha_hora"] for p in partidos), [f"2026-12-{d}T09:00:00" for d in (10, 11, 12, 13)])
        self.assertTrue(all(p["cancha_id"] == self.cancha1["id"] for p in partidos))

    def test_si_no_alcanzan_los_horarios_no_se_crea_nada(self):
        cuerpo = {"horas": ["09:00"], "canchas": [self.cancha1["id"]], "fecha_inicio": "2026-12-18"}  # solo 3 días
        r = self.fixture(cuerpo)
        self.assertEqual(r.status_code, 409)
        self.assertEqual(self.client.get(f"/fases/{self.fase_grupos['id']}/partidos").json(), [])

    def test_completa_solo_los_cruces_que_faltan(self):
        existente = self.programar_ok("A", "B", hora="2026-12-01T08:00:00")
        partidos = self.fixture_ok()
        self.assertEqual(len(partidos), 3)
        self.assertNotIn(frozenset(self.ids_de("A", "B")), self.parejas(partidos))
        todos = self.client.get(f"/fases/{self.fase_grupos['id']}/partidos").json()
        self.assertEqual(len(todos), 4)
        self.assertIn(existente["id"], [p["id"] for p in todos])
        self.assertFalse(hay_cruce(todos))  # respeta el partido que ya existía

    def test_segunda_llamada_no_duplica(self):
        self.fixture_ok()
        r = self.fixture()
        self.assertEqual(r.status_code, 409)
        self.assertIn("No hay cruces", r.json()["detail"])

    def test_asignar_arbitros(self):
        partidos = self.fixture_ok({"asignar_arbitros": True})
        self.assertTrue(all(p["arbitro_id"] in (self.arb1_id, self.arb2_id) for p in partidos))
        self.assertFalse(hay_cruce(partidos))

    def test_opciones_invalidas(self):
        casos = {
            "fecha antes del torneo": {"fecha_inicio": "2026-11-01"},
            "fecha después del torneo": {"fecha_inicio": "2026-12-25"},
            "cancha inexistente": {"canchas": [999]},
        }
        for nombre, cuerpo in casos.items():
            self.assertEqual(self.fixture(cuerpo).status_code, 400, nombre)
        self.client.patch(f"/canchas/{self.cancha2['id']}/estado", json={"estado_activo": False}, headers=self.h_admin)
        self.assertEqual(self.fixture({"canchas": [self.cancha2["id"]]}).status_code, 400)  # inhabilitada
        for malo in ({"horas": []}, {"horas": ["25:00"]}, {"canchas": []}, {"campo_raro": 1}):
            self.assertEqual(self.fixture(malo).status_code, 422, malo)

    def test_permisos_y_existencia(self):
        self.assertEqual(self.fixture(h=self.h_ent1).status_code, 403)
        self.assertEqual(self.fixture(h=self.h_arb1).status_code, 403)
        self.assertEqual(self.client.post(f"/fases/{self.fase_grupos['id']}/fixture").status_code, 401)
        self.assertEqual(self.fixture(fase={"id": 999}).status_code, 404)

    def test_una_fase_espera_a_la_anterior(self):
        r = self.fixture(fase=self.fase_final)
        self.assertEqual(r.status_code, 409)
        self.assertIn("Fase de Grupos", r.json()["detail"])

    # ---------- eliminatoria ----------
    def test_eliminatoria_parte_de_los_clasificados(self):
        self.jugar_toda_la_fase_de_grupos()
        self.cerrar_fase_de_grupos()  # clasifican A, B, D y E
        partidos = self.fixture_ok(fase=self.fase_final)
        cruces = {(p["equipo_local_id"], p["equipo_visitante_id"]) for p in partidos}
        self.assertEqual(cruces, {tuple(self.ids_de("A", "E")), tuple(self.ids_de("B", "D"))})  # primero vs último
        # La fase nueva empieza después del último partido de la anterior (el 2026-12-05).
        self.assertTrue(all(p["fecha_hora"] >= "2026-12-06T00:00:00" for p in partidos))
        self.assertFalse(hay_cruce(partidos))

    # ---------- programación general ----------
    def test_programacion_general_programa_la_primera_fase(self):
        ruta = f"/torneos/{self.torneo['id']}/programacion"
        self.assertEqual(self.client.post(ruta, headers=self.h_ent1).status_code, 403)
        self.assertEqual(self.client.post(ruta).status_code, 401)
        r = self.client.post(ruta, headers=self.h_admin)
        self.assertEqual(r.status_code, 201, r.text)
        self.assertEqual(len(r.json()), 4)
        self.assertTrue(all(p["fase_id"] == self.fase_grupos["id"] for p in r.json()))
        self.assertEqual(self.client.post(ruta, headers=self.h_admin).status_code, 409)  # ya tiene partidos
        self.assertEqual(self.client.post("/torneos/999/programacion", headers=self.h_admin).status_code, 404)
        otro = self.crear_torneo_api(nombre="Otra Copa")  # aún en Inscripciones
        self.assertEqual(self.client.post(f"/torneos/{otro['id']}/programacion", headers=self.h_admin).status_code, 409)

    def test_programacion_general_pasa_a_la_siguiente_fase(self):
        self.jugar_toda_la_fase_de_grupos()
        self.cerrar_fase_de_grupos()
        r = self.client.post(f"/torneos/{self.torneo['id']}/programacion", json={"asignar_arbitros": True}, headers=self.h_admin)
        self.assertEqual(r.status_code, 201, r.text)
        self.assertEqual(len(r.json()), 2)
        self.assertTrue(all(p["fase_id"] == self.fase_final["id"] for p in r.json()))


class FixtureSinGruposTest(BasePartidoTest):
    INICIALIZAR_GRUPOS = False

    def test_exige_armar_los_grupos_primero(self):
        r = self.client.post(f"/fases/{self.fase_grupos['id']}/fixture", headers=self.h_admin)
        self.assertEqual(r.status_code, 409)
        self.assertIn("grupos", r.json()["detail"])


if __name__ == "__main__":
    unittest.main()
