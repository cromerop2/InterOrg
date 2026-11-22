"""Pruebas de Jugadores: plantilla, edad, documento único por torneo, bloqueo, sanción y transferencias."""
import unittest
from datetime import date

from base_api import BaseInscripcionTest

from app.repositories.equipo_repository import EquipoRepository
from app.repositories.jugador_repository import JugadorRepository
from app.repositories.torneo_repository import TorneoRepository
from app.services.jugador_service import JugadorService


class JugadorApiTest(BaseInscripcionTest):
    def setUp(self):
        super().setUp()
        self.equipo = self.crear_equipo()
        self.ruta = f"/equipos/{self.equipo['id']}/jugadores"

    def agregar(self, datos, h=None, ruta=None):
        return self.client.post(ruta or self.ruta, json=datos, headers=h or self.h_ent1)

    def servicio(self, db):
        return JugadorService(JugadorRepository(db), EquipoRepository(db), TorneoRepository(db))

    # ---------- alta y permisos ----------
    def test_agregar_jugador(self):
        r = self.agregar(self.datos_jugador(1, numero_camiseta=10, posicion="Portero"))
        self.assertEqual(r.status_code, 201, r.text)
        jugador = r.json()
        self.assertEqual(jugador["equipo_id"], self.equipo["id"])
        self.assertTrue(jugador["estado_activo"])
        self.assertFalse(jugador["sancionado"])
        self.assertEqual(jugador["numero_camiseta"], 10)
        ruta = f"/jugadores/{jugador['id']}"
        self.assertEqual(self.client.get(ruta, headers=self.h_ent1).json(), jugador)
        self.assertEqual(self.client.get(ruta, headers=self.h_admin).status_code, 200)
        self.assertEqual(self.client.get(ruta, headers=self.h_ent2).status_code, 403)
        self.assertEqual(self.client.get(ruta).status_code, 401)
        self.assertEqual(self.client.get("/jugadores/999", headers=self.h_admin).status_code, 404)

    def test_solo_el_entrenador_dueno_agrega(self):
        datos = self.datos_jugador(1)
        self.assertEqual(self.agregar(datos, h=self.h_ent2).status_code, 403)
        self.assertEqual(self.agregar(datos, h=self.h_admin).status_code, 403)
        self.assertEqual(self.client.post(self.ruta, json=datos).status_code, 401)
        self.assertEqual(self.agregar(datos, ruta="/equipos/999/jugadores").status_code, 404)

    def test_la_plantilla_solo_la_ven_el_admin_y_el_dueno(self):
        self.agregar(self.datos_jugador(1))
        self.assertEqual(len(self.client.get(self.ruta, headers=self.h_ent1).json()), 1)
        self.assertEqual(len(self.client.get(self.ruta, headers=self.h_admin).json()), 1)
        self.assertEqual(self.client.get(self.ruta, headers=self.h_ent2).status_code, 403)
        self.assertEqual(self.client.get(self.ruta).status_code, 401)

    def test_validaciones_de_campos(self):
        for malo in (
            {"nombre_completo": "  "},
            {"identificacion": ""},
            {"numero_camiseta": 100},
            {"fecha_nacimiento": "2999-01-01"},
            {"campo_raro": 1},
        ):
            r = self.agregar(self.datos_jugador(1, **malo))
            self.assertEqual(r.status_code, 422, malo)

    # ---------- reglas ----------
    def test_maximo_de_jugadores(self):
        self.agregar_jugadores(self.equipo["id"], 3)  # el torneo de prueba permite 3
        self.assertEqual(self.agregar(self.datos_jugador(4)).status_code, 409)

    def test_documento_unico_por_torneo(self):
        self.agregar(self.datos_jugador(1))
        otro = self.crear_equipo(self.h_ent2, nombre="Los Tigres")
        r = self.agregar(self.datos_jugador(1), h=self.h_ent2, ruta=f"/equipos/{otro['id']}/jugadores")
        self.assertEqual(r.status_code, 409)  # mismo documento, otro equipo del mismo torneo
        self.assertEqual(self.agregar(self.datos_jugador(1, nombre_completo="Otro")).status_code, 409)

        # En otro torneo el mismo documento sí puede inscribirse.
        torneo2 = self.crear_torneo_api(nombre="Otra Copa")
        equipo2 = self.crear_equipo(self.h_ent2, nombre="Tigres B", torneo_id=torneo2["id"])
        r = self.agregar(self.datos_jugador(1), h=self.h_ent2, ruta=f"/equipos/{equipo2['id']}/jugadores")
        self.assertEqual(r.status_code, 201, r.text)

    def test_limite_de_edad_de_la_categoria(self):
        # Sub-17 se mide al inicio del torneo (2026-12-01): hasta 17 años cumplidos.
        self.assertEqual(self.agregar(self.datos_jugador(1, fecha_nacimiento="2008-12-02")).status_code, 201)
        r = self.agregar(self.datos_jugador(2, fecha_nacimiento="2008-12-01"))  # cumple 18 ese día
        self.assertEqual(r.status_code, 400)
        self.assertEqual(self.agregar(self.datos_jugador(3, fecha_nacimiento="2000-01-01")).status_code, 400)

    def test_categoria_sin_limite_de_edad(self):
        libre = self.crear_torneo_api(nombre="Copa Libre", categoria="Femenino Libre")
        equipo = self.crear_equipo(torneo_id=libre["id"], nombre="Veteranas")
        r = self.agregar(
            self.datos_jugador(1, fecha_nacimiento="1985-03-03"), ruta=f"/equipos/{equipo['id']}/jugadores"
        )
        self.assertEqual(r.status_code, 201, r.text)

    def test_validar_requisitos_edad(self):
        validar = JugadorService.validar_requisitos_edad
        referencia = date(2026, 12, 1)
        self.assertTrue(validar(date(2010, 5, 10), "Sub-17", referencia))
        self.assertTrue(validar(date(2009, 12, 1), "sub 17", referencia))  # 17 exactos
        self.assertFalse(validar(date(2008, 12, 1), "Sub-17", referencia))  # 18 exactos
        self.assertFalse(validar(date(2010, 5, 10), "SUB-15", referencia))
        self.assertTrue(validar(date(1970, 1, 1), "Femenino Libre", referencia))

    # ---------- baja ----------
    def test_dar_de_baja(self):
        jugador = self.agregar(self.datos_jugador(1)).json()
        ruta = f"/jugadores/{jugador['id']}/baja"
        self.assertEqual(self.client.post(ruta, headers=self.h_ent2).status_code, 403)
        self.assertEqual(self.client.post(ruta, headers=self.h_admin).status_code, 403)
        r = self.client.post(ruta, headers=self.h_ent1)
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.json()["estado_activo"])
        self.assertEqual(self.client.post(ruta, headers=self.h_ent1).status_code, 409)

        self.assertEqual(self.client.get(self.ruta, headers=self.h_ent1).json(), [])
        todos = self.client.get(self.ruta + "?solo_activos=false", headers=self.h_ent1).json()
        self.assertEqual([j["id"] for j in todos], [jugador["id"]])

    def test_la_baja_libera_cupo_y_documento(self):
        self.agregar_jugadores(self.equipo["id"], 3)
        jugadores = self.client.get(self.ruta, headers=self.h_ent1).json()
        self.client.post(f"/jugadores/{jugadores[0]['id']}/baja", headers=self.h_ent1)
        # Hay cupo de nuevo y el mismo documento puede volver a inscribirse.
        r = self.agregar(self.datos_jugador(1))
        self.assertEqual(r.status_code, 201, r.text)

    def test_equipo_habilitado_no_baja_del_minimo(self):
        equipo = self.habilitar_equipo(nombre="Habilitados", desde=20)
        jugadores = self.client.get(f"/equipos/{equipo['id']}/jugadores", headers=self.h_ent1).json()
        r = self.client.post(f"/jugadores/{jugadores[0]['id']}/baja", headers=self.h_ent1)
        self.assertEqual(r.status_code, 409)  # quedaría con 1 y el mínimo es 2

    # ---------- bloqueo ----------
    def test_plantilla_bloqueada_al_iniciar_el_torneo(self):
        equipo = self.habilitar_equipo(nombre="Habilitados", desde=20)
        ruta = f"/equipos/{equipo['id']}/jugadores"
        jugadores = self.client.get(ruta, headers=self.h_ent1).json()
        self.client.post(f"/torneos/{self.torneo['id']}/iniciar", headers=self.h_admin)

        self.assertEqual(self.agregar(self.datos_jugador(50), ruta=ruta).status_code, 409)
        self.assertEqual(self.client.post(f"/jugadores/{jugadores[0]['id']}/baja", headers=self.h_ent1).status_code, 409)
        # El equipo sin habilitar también quedó bloqueado.
        self.assertEqual(self.agregar(self.datos_jugador(1)).status_code, 409)

    def test_equipo_descalificado_no_modifica_su_plantilla(self):
        self.client.post(f"/equipos/{self.equipo['id']}/descalificar", headers=self.h_admin)
        self.assertEqual(self.agregar(self.datos_jugador(1)).status_code, 409)

    # ---------- sanción y elegibilidad ----------
    def test_sancion_y_elegibilidad(self):
        jugador = self.agregar(self.datos_jugador(1)).json()
        ruta = f"/jugadores/{jugador['id']}/sancion"
        self.assertEqual(self.client.patch(ruta, json={"sancionado": True}, headers=self.h_ent1).status_code, 403)
        self.assertEqual(self.client.patch("/jugadores/999/sancion", json={"sancionado": True}, headers=self.h_admin).status_code, 404)

        with self.Sesion() as db:
            self.assertTrue(self.servicio(db).verificar_elegibilidad(jugador["id"]))
        r = self.client.patch(ruta, json={"sancionado": True}, headers=self.h_admin)
        self.assertTrue(r.json()["sancionado"])
        with self.Sesion() as db:
            self.assertFalse(self.servicio(db).verificar_elegibilidad(jugador["id"]))
        self.client.patch(ruta, json={"sancionado": False}, headers=self.h_admin)
        self.client.post(f"/jugadores/{jugador['id']}/baja", headers=self.h_ent1)
        with self.Sesion() as db:
            self.assertFalse(self.servicio(db).verificar_elegibilidad(jugador["id"]))  # dado de baja

    # ---------- transferencias ----------
    def test_transferencia_no_permitida_por_las_reglas(self):
        jugador = self.agregar(self.datos_jugador(1)).json()
        otro = self.crear_equipo(self.h_ent2, nombre="Los Tigres")
        r = self.client.post(
            f"/jugadores/{jugador['id']}/transferir", json={"nuevo_equipo_id": otro["id"]}, headers=self.h_admin
        )
        self.assertEqual(r.status_code, 409)

    def test_transferencia_permitida(self):
        torneo = self.crear_torneo_api(
            nombre="Copa Libre", reglas={**self.REGLAS, "permite_transferencias": True}
        )
        origen = self.crear_equipo(nombre="Origen", torneo_id=torneo["id"])
        destino = self.crear_equipo(self.h_ent2, nombre="Destino", torneo_id=torneo["id"])
        jugador = self.agregar(
            self.datos_jugador(1), ruta=f"/equipos/{origen['id']}/jugadores"
        ).json()
        ruta = f"/jugadores/{jugador['id']}/transferir"

        self.assertEqual(self.client.post(ruta, json={"nuevo_equipo_id": destino["id"]}, headers=self.h_ent1).status_code, 403)
        self.assertEqual(self.client.post(ruta, json={"nuevo_equipo_id": origen["id"]}, headers=self.h_admin).status_code, 400)
        self.assertEqual(self.client.post(ruta, json={"nuevo_equipo_id": 999}, headers=self.h_admin).status_code, 404)
        # Equipo de otro torneo.
        self.assertEqual(self.client.post(ruta, json={"nuevo_equipo_id": self.equipo["id"]}, headers=self.h_admin).status_code, 400)

        r = self.client.post(ruta, json={"nuevo_equipo_id": destino["id"]}, headers=self.h_admin)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["equipo_id"], destino["id"])

    def test_transferencia_a_equipo_lleno(self):
        torneo = self.crear_torneo_api(
            nombre="Copa Libre", reglas={**self.REGLAS, "permite_transferencias": True}
        )
        origen = self.crear_equipo(nombre="Origen", torneo_id=torneo["id"])
        destino = self.crear_equipo(self.h_ent2, nombre="Destino", torneo_id=torneo["id"])
        jugador = self.agregar(self.datos_jugador(1), ruta=f"/equipos/{origen['id']}/jugadores").json()
        self.agregar_jugadores(destino["id"], 3, self.h_ent2, desde=10)  # máximo 3
        r = self.client.post(
            f"/jugadores/{jugador['id']}/transferir", json={"nuevo_equipo_id": destino["id"]}, headers=self.h_admin
        )
        self.assertEqual(r.status_code, 409)


if __name__ == "__main__":
    unittest.main()
