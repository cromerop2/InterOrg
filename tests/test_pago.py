"""Pruebas de Pagos: reporte del entrenador, validación del administrador y habilitación del equipo."""
import unittest
from decimal import Decimal

from base_api import BaseInscripcionTest

from app.core.dependencies import _armar_equipo_service


class PagoApiTest(BaseInscripcionTest):
    def setUp(self):
        super().setUp()
        self.equipo = self.crear_equipo()
        self.id_equipo = self.equipo["id"]

    def estado_equipo(self, id_equipo=None):
        r = self.client.get(f"/equipos/{id_equipo or self.id_equipo}", headers=self.h_admin)
        return r.json()["estado_inscripcion"]

    def estado_pago(self, id_pago):
        return self.client.get(f"/pagos/{id_pago}", headers=self.h_admin).json()["estado"]

    def auditar(self, id_pago, id_equipo=None, h=None):
        return self.client.patch(
            f"/equipos/{id_equipo or self.id_equipo}/auditar", json={"id_pago": id_pago}, headers=h or self.h_admin
        )

    def validar(self, id_pago, **cuerpo):
        return self.client.patch(f"/pagos/{id_pago}/validar", json=cuerpo, headers=self.h_admin)

    # ---------- reporte del entrenador ----------
    def test_registrar_comprobante(self):
        pago = self.comprobante_ok(self.id_equipo, comprobante_url="https://ejemplo.co/recibo.pdf")
        self.assertEqual(pago["estado"], "Pendiente")
        self.assertEqual(pago["equipo_id"], self.id_equipo)
        self.assertEqual(Decimal(str(pago["monto"])), Decimal("150000.00"))
        self.assertTrue(pago["fecha"])
        self.assertIsNone(pago["observaciones"])
        self.assertEqual(self.estado_equipo(), "Pago_Pendiente")
        self.comprobante_ok(self.id_equipo)  # un segundo pago no cambia el estado
        self.assertEqual(self.estado_equipo(), "Pago_Pendiente")

    def test_solo_el_entrenador_dueno_reporta(self):
        self.assertEqual(self.comprobante(self.id_equipo, h=self.h_ent2).status_code, 403)
        self.assertEqual(self.comprobante(self.id_equipo, h=self.h_admin).status_code, 403)
        self.assertEqual(self.client.post(f"/equipos/{self.id_equipo}/pagos", json={}).status_code, 401)
        self.assertEqual(self.comprobante(999).status_code, 404)

    def test_validaciones_del_comprobante(self):
        for malo in ({"monto": "0"}, {"monto": "-5"}, {"monto": "10.123"}, {"metodo_pago": " "}, {"estado": "Aprobado"}):
            self.assertEqual(self.comprobante(self.id_equipo, **malo).status_code, 422, malo)

    def test_referencia_duplicada_y_reutilizable_tras_rechazo(self):
        pago = self.comprobante_ok(self.id_equipo, referencia_transaccion="BANCO-1")
        otro = self.crear_equipo(self.h_ent2, nombre="Los Tigres")
        self.assertEqual(self.comprobante(otro["id"], h=self.h_ent2, referencia_transaccion="BANCO-1").status_code, 409)
        self.validar(pago["id"], aprobado=False, observaciones="Comprobante ilegible")
        r = self.comprobante(otro["id"], h=self.h_ent2, referencia_transaccion="BANCO-1")
        self.assertEqual(r.status_code, 201, r.text)

    # ---------- auditoría y habilitación ----------
    def test_auditar_exige_plantilla_completa(self):
        pago = self.comprobante_ok(self.id_equipo)
        self.agregar_jugadores(self.id_equipo, 1)  # el mínimo es 2
        r = self.auditar(pago["id"])
        self.assertEqual(r.status_code, 400)
        self.assertIn("Plantilla incompleta", r.json()["detail"])
        self.assertEqual(self.estado_pago(pago["id"]), "Pendiente")
        self.assertEqual(self.estado_equipo(), "Pago_Pendiente")

    def test_auditar_habilita_el_equipo_y_aprueba_el_pago(self):
        self.agregar_jugadores(self.id_equipo, 2)
        pago = self.comprobante_ok(self.id_equipo)
        with self.Sesion() as db:
            self.assertFalse(_armar_equipo_service(db).verificar_solvencia(self.id_equipo))

        r = self.auditar(pago["id"])
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["estado_inscripcion"], "Habilitado")
        self.assertEqual(self.estado_pago(pago["id"]), "Aprobado")
        with self.Sesion() as db:
            servicio = _armar_equipo_service(db)
            self.assertTrue(servicio.verificar_solvencia(self.id_equipo))
            self.assertTrue(servicio.validar_minimo_jugadores(self.id_equipo))

        self.assertEqual(self.auditar(pago["id"]).status_code, 409)  # ya habilitado
        self.assertEqual(self.comprobante(self.id_equipo).status_code, 409)  # ya no recibe pagos

    def test_auditar_solo_el_administrador(self):
        pago = self.comprobante_ok(self.id_equipo)
        self.assertEqual(self.auditar(pago["id"], h=self.h_ent1).status_code, 403)
        self.assertEqual(self.client.patch(f"/equipos/{self.id_equipo}/auditar", json={"id_pago": pago["id"]}).status_code, 401)

    def test_auditar_con_pago_ajeno_o_inexistente(self):
        self.agregar_jugadores(self.id_equipo, 2)
        otro = self.crear_equipo(self.h_ent2, nombre="Los Tigres")
        pago_ajeno = self.comprobante_ok(otro["id"], h=self.h_ent2)
        self.assertEqual(self.auditar(pago_ajeno["id"]).status_code, 400)
        self.assertEqual(self.auditar(999).status_code, 404)
        self.assertEqual(self.estado_pago(pago_ajeno["id"]), "Pendiente")

    def test_no_se_audita_con_el_torneo_cancelado(self):
        self.agregar_jugadores(self.id_equipo, 2)
        pago = self.comprobante_ok(self.id_equipo)
        self.client.post(f"/torneos/{self.torneo['id']}/cancelar", headers=self.h_admin)
        self.assertEqual(self.auditar(pago["id"]).status_code, 409)

    # ---------- validar pago ----------
    def test_validar_pago_aprobando(self):
        self.agregar_jugadores(self.id_equipo, 2)
        pago = self.comprobante_ok(self.id_equipo)
        r = self.validar(pago["id"], aprobado=True)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["estado"], "Aprobado")
        self.assertEqual(self.estado_equipo(), "Habilitado")

    def test_aprobar_con_plantilla_incompleta_no_cambia_nada(self):
        pago = self.comprobante_ok(self.id_equipo)
        self.assertEqual(self.validar(pago["id"], aprobado=True).status_code, 400)
        self.assertEqual(self.estado_pago(pago["id"]), "Pendiente")
        self.assertEqual(self.estado_equipo(), "Pago_Pendiente")

    def test_validar_pago_rechazando(self):
        pago = self.comprobante_ok(self.id_equipo)
        self.assertEqual(self.validar(pago["id"], aprobado=False).status_code, 422)  # exige motivo
        r = self.validar(pago["id"], aprobado=False, observaciones="Comprobante ilegible")
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["estado"], "Rechazado")
        self.assertEqual(r.json()["observaciones"], "Comprobante ilegible")
        self.assertEqual(self.estado_equipo(), "Preinscrito")  # debe reportar un pago nuevo
        self.assertEqual(self.validar(pago["id"], aprobado=True).status_code, 409)  # ya revisado

    def test_rechazar_con_otro_pago_pendiente_mantiene_el_estado(self):
        primero = self.comprobante_ok(self.id_equipo)
        self.comprobante_ok(self.id_equipo)
        self.validar(primero["id"], aprobado=False, observaciones="Monto incorrecto")
        self.assertEqual(self.estado_equipo(), "Pago_Pendiente")

    def test_validar_pago_solo_administrador_y_existente(self):
        pago = self.comprobante_ok(self.id_equipo)
        r = self.client.patch(f"/pagos/{pago['id']}/validar", json={"aprobado": True}, headers=self.h_ent1)
        self.assertEqual(r.status_code, 403)
        self.assertEqual(self.validar(999, aprobado=True).status_code, 404)

    # ---------- consultas ----------
    def test_consultas_de_pagos(self):
        pago = self.comprobante_ok(self.id_equipo)
        rechazado = self.comprobante_ok(self.id_equipo)
        self.validar(rechazado["id"], aprobado=False, observaciones="Duplicado")

        todos = self.client.get("/pagos/", headers=self.h_admin).json()
        self.assertEqual([p["id"] for p in todos], [pago["id"], rechazado["id"]])
        pendientes = self.client.get("/pagos/?estado=Pendiente", headers=self.h_admin).json()
        self.assertEqual([p["id"] for p in pendientes], [pago["id"]])
        self.assertEqual(self.client.get("/pagos/?estado=Inventado", headers=self.h_admin).status_code, 422)
        self.assertEqual(self.client.get("/pagos/", headers=self.h_ent1).status_code, 403)

        ruta = f"/equipos/{self.id_equipo}/pagos"
        self.assertEqual(len(self.client.get(ruta, headers=self.h_ent1).json()), 2)
        self.assertEqual(len(self.client.get(ruta, headers=self.h_admin).json()), 2)
        self.assertEqual(self.client.get(ruta, headers=self.h_ent2).status_code, 403)

        ruta = f"/pagos/{pago['id']}"
        self.assertEqual(self.client.get(ruta, headers=self.h_ent1).status_code, 200)
        self.assertEqual(self.client.get(ruta, headers=self.h_ent2).status_code, 403)
        self.assertEqual(self.client.get(ruta).status_code, 401)
        self.assertEqual(self.client.get("/pagos/999", headers=self.h_admin).status_code, 404)


if __name__ == "__main__":
    unittest.main()
