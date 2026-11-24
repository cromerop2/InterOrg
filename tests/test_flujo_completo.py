"""Flujo completo, solo por la API: crear torneo → inscribir equipos → pagar → programar → jugar →
cerrar acta → tabla actualizada (y luego cerrar el grupo y la fase)."""
import unittest

from base_api import CLAVE, BaseApiTest


class FlujoCompletoTest(BaseApiTest):
    def post(self, ruta, cuerpo=None, h=None, esperado=201):
        r = self.client.post(ruta, json=cuerpo, headers=h or self.h_admin)
        self.assertEqual(r.status_code, esperado, f"POST {ruta}: {r.text}")
        return r.json() if r.content else None

    def put(self, ruta, cuerpo, h, esperado=200):
        r = self.client.put(ruta, json=cuerpo, headers=h)
        self.assertEqual(r.status_code, esperado, f"PUT {ruta}: {r.text}")
        return r.json()

    def patch(self, ruta, cuerpo, h=None, esperado=200):
        r = self.client.patch(ruta, json=cuerpo, headers=h or self.h_admin)
        self.assertEqual(r.status_code, esperado, f"PATCH {ruta}: {r.text}")
        return r.json()

    def get(self, ruta, h=None, esperado=200):
        r = self.client.get(ruta, headers=h)
        self.assertEqual(r.status_code, esperado, f"GET {ruta}: {r.text}")
        return r.json()

    def crear_cuenta(self, rol, email, **extra):
        self.post("/usuarios/", {
            "rol": rol, "nombre_completo": f"{rol} {email}", "email": email,
            "telefono_contacto": "3000000000", "password": CLAVE, **extra,
        })
        return self.cabecera(email)

    def inscribir_y_habilitar(self, colegio, torneo, h_entrenador, nombre, desde):
        equipo = self.post("/equipos/", {"colegio_id": colegio["id"], "torneo_id": torneo["id"], "nombre": nombre}, h_entrenador)
        self.assertEqual(equipo["estado_inscripcion"], "Preinscrito")
        for n in range(desde, desde + 3):
            self.post(f"/equipos/{equipo['id']}/jugadores", {
                "nombre_completo": f"Jugador {n}", "identificacion": f"90{n:04d}", "fecha_nacimiento": "2010-03-15",
            }, h_entrenador)
        pago = self.post(f"/equipos/{equipo['id']}/pagos", {
            "monto": "150000.00", "metodo_pago": "Transferencia", "referencia_transaccion": f"REF-{nombre}",
        }, h_entrenador)
        self.assertEqual(self.get(f"/equipos/{equipo['id']}", h_entrenador)["estado_inscripcion"], "Pago_Pendiente")
        validado = self.patch(f"/pagos/{pago['id']}/validar", {"aprobado": True})
        self.assertEqual(validado["estado"], "Aprobado")
        self.assertEqual(self.get(f"/equipos/{equipo['id']}", h_entrenador)["estado_inscripcion"], "Habilitado")
        return equipo

    def test_del_torneo_a_la_tabla_de_posiciones(self):
        # 1. El administrador prepara el torneo.
        colegio = self.post("/colegios/", {
            "nombre": "Colegio Flujo", "direccion": "Calle 1", "representante_legal": "Rector", "telefono_contacto": "3001112233",
        })
        torneo = self.post("/torneos/", {
            "nombre": "Copa Flujo", "categoria": "Sub-17", "fecha_inicio": "2026-12-01", "fecha_fin": "2026-12-20",
            "reglas": {"min_jugadores": 2, "max_jugadores": 5, "min_equipos": 2, "titulares": 2, "max_suplentes": 1},
        })
        self.assertEqual(torneo["estado"], "Inscripciones")
        fase = self.post(f"/torneos/{torneo['id']}/fases", {"nombre": "Grupos", "tipo_formato": "Grupos"})
        cancha = self.post("/canchas/", {"nombre": "Cancha Central", "direccion_sede": "Complejo Norte"})

        # 2. Se crean las cuentas desde la API.
        h_ent1 = self.crear_cuenta("Entrenador", "e1@flujo.co", colegio_id=colegio["id"])
        h_ent2 = self.crear_cuenta("Entrenador", "e2@flujo.co")
        h_arb = self.crear_cuenta("Arbitro", "arb@flujo.co")
        arbitro_id = self.get("/auth/me", h_arb)["id"]

        # 3. Inscripción y pago de dos equipos.
        local = self.inscribir_y_habilitar(colegio, torneo, h_ent1, "Halcones", 1)
        visitante = self.inscribir_y_habilitar(colegio, torneo, h_ent2, "Tigres", 10)
        self.assertEqual(len(self.get(f"/torneos/{torneo['id']}/equipos", self.h_admin)), 2)

        # 4. Inicia el torneo y se arma el grupo.
        self.assertEqual(self.post(f"/torneos/{torneo['id']}/iniciar", h=self.h_admin, esperado=200)["estado"], "En_Curso")
        self.post(f"/fases/{fase['id']}/grupos", {"grupos": {"Grupo A": [local["id"], visitante["id"]]}})

        # 5. Programación (con árbitro) y planillas de los dos entrenadores.
        partido = self.post("/partidos/", {
            "fase_id": fase["id"], "equipo_local_id": local["id"], "equipo_visitante_id": visitante["id"],
            "cancha_id": cancha["id"], "fecha_hora": "2026-12-05T10:00:00", "arbitro_id": arbitro_id,
        })
        self.assertEqual(partido["estado"], "Programado")
        self.assertEqual(self.get(f"/partidos/{partido['id']}/marcador")["goles_local"], 0)
        goleador = None
        for equipo, h in ((local, h_ent1), (visitante, h_ent2)):
            jugadores = self.get(f"/equipos/{equipo['id']}/jugadores", h)
            if equipo is local:
                goleador = jugadores[0]["id"]
            self.put(f"/partidos/{partido['id']}/equipos/{equipo['id']}/alineacion", {
                "jugadores": [{"jugador_id": j["id"], "es_titular": i < 2} for i, j in enumerate(jugadores)],
            }, h)

        # 6. El día del partido: inicia, el árbitro registra goles y cierra el acta.
        self.assertEqual(self.post(f"/partidos/{partido['id']}/iniciar", h=h_arb, esperado=200)["estado"], "En_Juego")
        for minuto in (12, 40):
            self.post(f"/partidos/{partido['id']}/eventos", {
                "equipo_id": local["id"], "jugador_id": goleador, "tipo_evento": "Gol", "minuto_ocurrencia": minuto,
            }, h_arb)
        self.assertEqual(self.get(f"/partidos/{partido['id']}/marcador")["goles_local"], 2)
        # La tabla no cambia hasta cerrar el acta.
        self.assertEqual(self.get(f"/fases/{fase['id']}/tablas")[0]["filas"][0]["partidos_jugados"], 0)
        cerrado = self.post(f"/partidos/{partido['id']}/cerrar", h=h_arb, esperado=200)
        self.assertEqual(cerrado["estado"], "Finalizado")
        self.assertTrue(self.get(f"/partidos/{partido['id']}/marcador")["es_resultado_final"])

        # 7. Tabla actualizada, goleadores y estadísticas del entrenador.
        filas = self.get(f"/fases/{fase['id']}/tablas")[0]["filas"]
        self.assertEqual([f["equipo_id"] for f in filas], [local["id"], visitante["id"]])
        ganador, perdedor = filas
        self.assertEqual((ganador["partidos_jugados"], ganador["partidos_ganados"], ganador["puntos"]), (1, 1, 3))
        self.assertEqual((ganador["goles_a_favor"], ganador["goles_en_contra"], ganador["diferencia_goles"]), (2, 0, 2))
        self.assertEqual((perdedor["partidos_perdidos"], perdedor["puntos"], perdedor["diferencia_goles"]), (1, 0, -2))
        self.assertEqual(self.get(f"/torneos/{torneo['id']}/goleadores")[0]["goles"], 2)
        self.assertEqual(self.get(f"/equipos/{local['id']}/estadisticas", h_ent1)[0]["puntos"], 3)

        # 8. Se cierra el grupo, la fase y el torneo.
        tabla_id = self.get(f"/fases/{fase['id']}/tablas")[0]["id"]
        self.assertEqual(self.post(f"/tablas/{tabla_id}/cerrar", h=self.h_admin, esperado=200)["clasificados"][0], local["id"])
        self.assertEqual(self.post(f"/fases/{fase['id']}/cerrar", h=self.h_admin, esperado=200)["estado"], "Finalizada")
        self.assertEqual(self.post(f"/torneos/{torneo['id']}/finalizar", h=self.h_admin, esperado=200)["estado"], "Finalizado")


if __name__ == "__main__":
    unittest.main()
