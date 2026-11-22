"""Pruebas de Equipos: inscripción, consulta, descalificación, vínculo con colegio e inicio del torneo."""
import unittest

from base_api import BaseInscripcionTest


class EquipoApiTest(BaseInscripcionTest):
    def test_registrar_equipo(self):
        equipo = self.crear_equipo()
        self.assertEqual(equipo["estado_inscripcion"], "Preinscrito")
        self.assertEqual(equipo["entrenador_id"], self.ent1_id)  # sale de la sesión, no del cuerpo
        self.assertEqual(equipo["torneo_id"], self.torneo["id"])
        self.assertFalse(equipo["plantilla_bloqueada"])
        self.assertIsNone(equipo["escudo_url"])

    def test_solo_un_entrenador_registra_equipos(self):
        datos = {"colegio_id": self.colegio["id"], "torneo_id": self.torneo["id"], "nombre": "X"}
        self.assertEqual(self.client.post("/equipos/", json=datos).status_code, 401)
        self.assertEqual(self.client.post("/equipos/", json=datos, headers=self.h_admin).status_code, 403)
        self.crear_usuario("Arbitro", "arb@torneo.edu.co")
        h = self.cabecera("arb@torneo.edu.co")
        self.assertEqual(self.client.post("/equipos/", json=datos, headers=h).status_code, 403)

    def test_validaciones_del_registro(self):
        self.crear_equipo()
        datos = {"colegio_id": self.colegio["id"], "torneo_id": self.torneo["id"], "nombre": "Los Halcones"}

        r = self.client.post("/equipos/", json=datos, headers=self.h_ent2)
        self.assertEqual(r.status_code, 409)  # nombre repetido en el mismo torneo
        otro_torneo = self.crear_torneo_api(nombre="Otra Copa")
        self.crear_equipo(self.h_ent2, torneo_id=otro_torneo["id"])  # el mismo nombre en otro torneo sí

        r = self.client.post("/equipos/", json={**datos, "nombre": "A", "colegio_id": 999}, headers=self.h_ent1)
        self.assertEqual(r.status_code, 404)
        r = self.client.post("/equipos/", json={**datos, "nombre": "A", "torneo_id": 999}, headers=self.h_ent1)
        self.assertEqual(r.status_code, 404)
        inactivo = self.crear_colegio_api("Colegio Cerrado", estado_activo=False)
        r = self.client.post("/equipos/", json={**datos, "nombre": "A", "colegio_id": inactivo["id"]}, headers=self.h_ent1)
        self.assertEqual(r.status_code, 400)
        r = self.client.post("/equipos/", json={**datos, "nombre": "A", "entrenador_id": 1}, headers=self.h_ent1)
        self.assertEqual(r.status_code, 422)  # el entrenador no se elige

    def test_torneo_que_no_recibe_inscripciones(self):
        self.client.post(f"/torneos/{self.torneo['id']}/cancelar", headers=self.h_admin)
        datos = {"colegio_id": self.colegio["id"], "torneo_id": self.torneo["id"], "nombre": "Tarde"}
        self.assertEqual(self.client.post("/equipos/", json=datos, headers=self.h_ent1).status_code, 409)

    def test_entrenador_vinculado_a_otro_colegio(self):
        otro = self.crear_colegio_api("Colegio Norte")
        self.crear_usuario("Entrenador", "ent3@torneo.edu.co", colegio_id=otro["id"])
        h3 = self.cabecera("ent3@torneo.edu.co")
        datos = {"colegio_id": self.colegio["id"], "torneo_id": self.torneo["id"], "nombre": "Intruso"}
        self.assertEqual(self.client.post("/equipos/", json=datos, headers=h3).status_code, 403)
        datos["colegio_id"] = otro["id"]
        self.assertEqual(self.client.post("/equipos/", json=datos, headers=h3).status_code, 201)

    def test_consulta_de_equipos(self):
        equipo = self.crear_equipo()
        ruta = f"/equipos/{equipo['id']}"
        self.assertEqual(self.client.get(ruta, headers=self.h_ent1).json(), equipo)
        self.assertEqual(self.client.get(ruta, headers=self.h_admin).status_code, 200)
        self.assertEqual(self.client.get(ruta, headers=self.h_ent2).status_code, 403)
        self.assertEqual(self.client.get(ruta).status_code, 401)
        self.assertEqual(self.client.get("/equipos/999", headers=self.h_admin).status_code, 404)

    def test_listar_por_torneo_y_por_colegio(self):
        equipo = self.crear_equipo()
        ruta = f"/torneos/{self.torneo['id']}/equipos"
        self.assertEqual(self.client.get(ruta, headers=self.h_ent2).json(), [equipo])  # cualquier sesión
        self.assertEqual(self.client.get(ruta).status_code, 401)
        self.assertEqual(self.client.get("/torneos/999/equipos", headers=self.h_admin).status_code, 404)

        ruta = f"/colegios/{self.colegio['id']}/equipos"
        self.assertEqual(self.client.get(ruta, headers=self.h_admin).json(), [equipo])
        self.assertEqual(self.client.get(ruta, headers=self.h_ent1).status_code, 403)
        self.assertEqual(self.client.get("/colegios/999/equipos", headers=self.h_admin).status_code, 404)

    def test_descalificar(self):
        equipo = self.crear_equipo()
        ruta = f"/equipos/{equipo['id']}/descalificar"
        self.assertEqual(self.client.post(ruta, headers=self.h_ent1).status_code, 403)
        r = self.client.post(ruta, headers=self.h_admin)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["estado_inscripcion"], "Descalificado")
        self.assertEqual(self.client.post(ruta, headers=self.h_admin).status_code, 409)

    def test_vincular_entrenador_a_colegio(self):
        ruta = f"/colegios/{self.colegio['id']}/entrenadores/{self.ent1_id}"
        self.assertEqual(self.client.put(ruta, headers=self.h_ent1).status_code, 403)
        r = self.client.put(ruta, headers=self.h_admin)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["colegio_id"], self.colegio["id"])

        # Ya vinculado, solo puede inscribir equipos de ese colegio.
        otro = self.crear_colegio_api("Colegio Norte")
        datos = {"colegio_id": otro["id"], "torneo_id": self.torneo["id"], "nombre": "Ajeno"}
        self.assertEqual(self.client.post("/equipos/", json=datos, headers=self.h_ent1).status_code, 403)

    def test_vincular_entrenador_validaciones(self):
        arbitro_id = self.crear_usuario("Arbitro", "arb@torneo.edu.co")
        c = self.colegio["id"]
        self.assertEqual(self.client.put(f"/colegios/{c}/entrenadores/{arbitro_id}", headers=self.h_admin).status_code, 400)
        self.assertEqual(self.client.put(f"/colegios/{c}/entrenadores/999", headers=self.h_admin).status_code, 404)
        self.assertEqual(self.client.put(f"/colegios/999/entrenadores/{self.ent1_id}", headers=self.h_admin).status_code, 404)
        inactivo = self.crear_colegio_api("Colegio Cerrado", estado_activo=False)
        r = self.client.put(f"/colegios/{inactivo['id']}/entrenadores/{self.ent1_id}", headers=self.h_admin)
        self.assertEqual(r.status_code, 400)


class IniciarTorneoTest(BaseInscripcionTest):
    def ruta(self):
        return f"/torneos/{self.torneo['id']}/iniciar"

    def test_exige_el_minimo_de_equipos_habilitados(self):
        r = self.client.post(self.ruta(), headers=self.h_admin)
        self.assertEqual(r.status_code, 400)  # no hay equipos
        self.crear_equipo()  # Preinscrito no cuenta
        self.assertEqual(self.client.post(self.ruta(), headers=self.h_admin).status_code, 400)
        self.assertEqual(self.client.get(f"/torneos/{self.torneo['id']}").json()["estado"], "Inscripciones")

    def test_inicia_y_bloquea_todas_las_plantillas(self):
        habilitado = self.habilitar_equipo()
        otro = self.crear_equipo(self.h_ent2, nombre="Sin Pago")  # no habilitado
        self.assertEqual(self.client.post(self.ruta(), headers=self.h_ent1).status_code, 403)

        r = self.client.post(self.ruta(), headers=self.h_admin)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["estado"], "En_Curso")
        for id_equipo in (habilitado["id"], otro["id"]):
            equipo = self.client.get(f"/equipos/{id_equipo}", headers=self.h_admin).json()
            self.assertTrue(equipo["plantilla_bloqueada"])

        self.assertEqual(self.client.post(self.ruta(), headers=self.h_admin).status_code, 409)
        datos = {"colegio_id": self.colegio["id"], "torneo_id": self.torneo["id"], "nombre": "Tarde"}
        self.assertEqual(self.client.post("/equipos/", json=datos, headers=self.h_ent2).status_code, 409)

    def test_el_minimo_de_equipos_es_configurable(self):
        torneo = self.crear_torneo_api(nombre="Copa de Dos", reglas={**self.REGLAS, "min_equipos": 2})
        self.habilitar_equipo(torneo_id=torneo["id"])
        ruta = f"/torneos/{torneo['id']}/iniciar"
        self.assertEqual(self.client.post(ruta, headers=self.h_admin).status_code, 400)  # 1 de 2
        self.habilitar_equipo(nombre="Segundo", desde=10, h=self.h_ent2, torneo_id=torneo["id"])
        self.assertEqual(self.client.post(ruta, headers=self.h_admin).status_code, 200)


if __name__ == "__main__":
    unittest.main()
