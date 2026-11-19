"""Pruebas de Canchas: permisos, CRUD y estado."""
import unittest

from base_api import BaseApiTest


class CanchaApiTest(BaseApiTest):
    def setUp(self):
        super().setUp()
        self.datos = {"nombre": "Cancha Principal", "direccion_sede": "Complejo Norte", "tipo_superficie": "Sintética"}

    def crear(self, **cambios):
        r = self.client.post("/canchas/", json={**self.datos, **cambios}, headers=self.h_admin)
        self.assertEqual(r.status_code, 201, r.text)
        return r.json()

    def test_crear_y_consultar(self):
        cancha = self.crear()
        self.assertIsInstance(cancha["id"], int)
        self.assertTrue(cancha["estado_activo"])
        r = self.client.get(f"/canchas/{cancha['id']}", headers=self.h_admin)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), cancha)

    def test_superficie_es_opcional(self):
        cancha = self.crear(tipo_superficie=None)
        self.assertIsNone(cancha["tipo_superficie"])

    def test_permisos(self):
        self.assertEqual(self.client.get("/canchas/").status_code, 401)
        self.assertEqual(self.client.post("/canchas/", json=self.datos).status_code, 401)

        self.crear_usuario("Arbitro", "arb@torneo.edu.co")
        h = self.cabecera("arb@torneo.edu.co")
        cancha = self.crear()
        # Cualquier usuario con sesión consulta; solo el Administrador modifica.
        self.assertEqual(self.client.get("/canchas/", headers=h).status_code, 200)
        self.assertEqual(self.client.get(f"/canchas/{cancha['id']}", headers=h).status_code, 200)
        self.assertEqual(self.client.post("/canchas/", json=self.datos, headers=h).status_code, 403)
        self.assertEqual(self.client.patch(f"/canchas/{cancha['id']}", json={"nombre": "X"}, headers=h).status_code, 403)
        self.assertEqual(
            self.client.patch(f"/canchas/{cancha['id']}/estado", json={"estado_activo": False}, headers=h).status_code, 403
        )

    def test_listar_solo_activas_por_defecto(self):
        activa = self.crear()
        inactiva = self.crear(nombre="Sintética Norte")
        self.client.patch(f"/canchas/{inactiva['id']}/estado", json={"estado_activo": False}, headers=self.h_admin)
        r = self.client.get("/canchas/", headers=self.h_admin)
        self.assertEqual([c["id"] for c in r.json()], [activa["id"]])
        r = self.client.get("/canchas/?solo_activas=false", headers=self.h_admin)
        self.assertEqual([c["id"] for c in r.json()], [activa["id"], inactiva["id"]])

    def test_actualizar_detalles_parcial(self):
        cancha = self.crear()
        r = self.client.patch(
            f"/canchas/{cancha['id']}", json={"direccion_sede": "Sede Sur", "tipo_superficie": None}, headers=self.h_admin
        )
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json(), {**cancha, "direccion_sede": "Sede Sur", "tipo_superficie": None})

    def test_inhabilitar_y_rehabilitar(self):
        cancha = self.crear()
        ruta = f"/canchas/{cancha['id']}/estado"
        r = self.client.patch(ruta, json={"estado_activo": False}, headers=self.h_admin)
        self.assertFalse(r.json()["estado_activo"])
        r = self.client.patch(ruta, json={"estado_activo": True}, headers=self.h_admin)
        self.assertTrue(r.json()["estado_activo"])

    def test_inexistente(self):
        self.assertEqual(self.client.get("/canchas/999", headers=self.h_admin).status_code, 404)
        self.assertEqual(self.client.patch("/canchas/999", json={"nombre": "X"}, headers=self.h_admin).status_code, 404)
        self.assertEqual(
            self.client.patch("/canchas/999/estado", json={"estado_activo": False}, headers=self.h_admin).status_code, 404
        )

    def test_validaciones(self):
        for malo in ({"nombre": "   "}, {"direccion_sede": ""}, {"campo_raro": 1}):
            r = self.client.post("/canchas/", json={**self.datos, **malo}, headers=self.h_admin)
            self.assertEqual(r.status_code, 422, malo)
        cancha = self.crear()
        r = self.client.patch(f"/canchas/{cancha['id']}", json={"nombre": None}, headers=self.h_admin)
        self.assertEqual(r.status_code, 422)
        r = self.client.patch(f"/canchas/{cancha['id']}", json={"estado_activo": False}, headers=self.h_admin)
        self.assertEqual(r.status_code, 422)  # el estado se cambia en /estado
        self.assertEqual(self.client.get("/canchas/0", headers=self.h_admin).status_code, 422)


if __name__ == "__main__":
    unittest.main()
