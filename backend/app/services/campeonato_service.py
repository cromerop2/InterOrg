"""Grupos, fixture, resultados y progresión eliminatoria del campeonato."""
from datetime import timezone
from fastapi import HTTPException
from app.models.equipo_model import EquipoModel
from app.models.fase_model import FaseModel
from app.models.grupo_model import GrupoModel
from app.models.partido_model import PartidoModel
from app.services.transaction import transaccion
from sqlalchemy import or_


class CampeonatoService:
    def __init__(self, repository):
        self.repository = repository

    @staticmethod
    def _exigir(condicion, mensaje, codigo=409):
        if not condicion:
            raise HTTPException(codigo, mensaje)

    def obtener_torneo(self, id_torneo, bloquear=False):
        torneo = self.repository.obtener_torneo(id_torneo, bloquear)
        if torneo is None:
            raise HTTPException(404, "Campeonato no existe.")
        return torneo

    def obtener_torneos(self, estado=None):
        return self.repository.obtener_torneos(estado)

    @transaccion
    def crear_torneo(self, datos):
        return self.repository.crear_torneo(datos)

    def obtener_inscripciones(self, id_torneo):
        self.obtener_torneo(id_torneo)
        return self.repository.obtener_inscripciones(id_torneo)

    @transaccion
    def inscribir_equipo(self, id_torneo, datos):
        torneo = self.obtener_torneo(id_torneo, bloquear=True)
        self._exigir(torneo.estado == "Inscripciones", "Las inscripciones ya están cerradas.")
        equipo = self.repository.db.get(EquipoModel, datos.equipo_id)
        self._exigir(equipo is not None, "Equipo no existe.", 404)
        self._exigir(equipo.estado_activo, "El equipo está inactivo.")
        return self.repository.inscribir_equipo(id_torneo, equipo.id)

    @transaccion
    def retirar_equipo(self, id_torneo, id_equipo):
        torneo = self.obtener_torneo(id_torneo, bloquear=True)
        self._exigir(torneo.estado == "Inscripciones", "No se puede retirar un equipo con fixture generado.")
        inscripcion = next((i for i in self.repository.obtener_inscripciones(id_torneo)
                            if i.equipo_id == id_equipo), None)
        self._exigir(inscripcion is not None, "La inscripción no existe.", 404)
        self.repository.retirar_equipo(inscripcion)

    @staticmethod
    def _round_robin(equipos):
        """Método circular: cada pareja juega una vez y cada equipo descansa si es impar."""
        rueda = list(equipos)
        if len(rueda) % 2:
            rueda.append(None)
        cruces = []
        for jornada in range(1, len(rueda)):
            for indice in range(len(rueda) // 2):
                local, visitante = rueda[indice], rueda[-indice - 1]
                if local is not None and visitante is not None:
                    if jornada % 2 == 0:
                        local, visitante = visitante, local
                    cruces.append((jornada, local, visitante))
            rueda = [rueda[0], rueda[-1], *rueda[1:-1]]
        return cruces

    @transaccion
    def generar_fixture(self, id_torneo):
        """Distribuye por orden de inscripción, en rondas, para equilibrar los grupos."""
        torneo = self.obtener_torneo(id_torneo, bloquear=True)
        self._exigir(torneo.estado == "Inscripciones", "El fixture ya fue generado o el torneo está cerrado.")
        inscripciones = self.repository.obtener_inscripciones(id_torneo)
        minimo = max(2, torneo.clasifican_por_grupo)
        self._exigir(len(inscripciones) >= torneo.numero_grupos * minimo,
                      "Faltan equipos: cada grupo necesita al menos dos y suficientes clasificados.")
        equipos = self.repository._equipos([i.equipo_id for i in inscripciones])
        self._exigir(all(e.estado_activo for e in equipos.values()), "Hay equipos inscritos inactivos.")
        fase = FaseModel(torneo_id=id_torneo, nombre="Fase de grupos", tipo="Grupos", orden=1)
        grupos, partidos = [], []
        numero = 1
        for indice in range(torneo.numero_grupos):
            miembros = inscripciones[indice::torneo.numero_grupos]
            grupo = GrupoModel(nombre=f"Grupo {indice + 1}")
            grupos.append((grupo, miembros))
            for jornada, local, visitante in self._round_robin([i.equipo_id for i in miembros]):
                partido = PartidoModel(torneo_id=id_torneo, numero=numero, jornada=jornada,
                                       equipo_local_id=local, equipo_visitante_id=visitante)
                partidos.append((partido, grupo))
                numero += 1
        self.repository.generar_fixture(fase, grupos, partidos)
        torneo.estado = "En_Curso"
        # SessionLocal desactiva autoflush: guardar antes de volver a consultar
        # evita que populate_existing reemplace el cambio todavía pendiente.
        self.repository.db.flush()
        return self.obtener_fixture(id_torneo)

    def _vistas_partidos(self, partidos):
        """Incluye nombres para que la app no tenga que hacer consultas por cada ID."""
        equipos = self.repository._equipos({i for p in partidos for i in (p.equipo_local_id, p.equipo_visitante_id)})
        fases = {f.id: f for f in self.repository.db.query(FaseModel).filter(
            FaseModel.id.in_({p.fase_id for p in partidos})).all()}
        grupos = {g.id: g.nombre for g in self.repository.db.query(GrupoModel).filter(
            GrupoModel.id.in_({p.grupo_id for p in partidos if p.grupo_id})).all()}
        campos = ("id", "torneo_id", "fase_id", "grupo_id", "numero", "jornada", "equipo_local_id",
                  "equipo_visitante_id", "fecha_hora", "sede", "estado", "goles_local",
                  "goles_visitante", "penales_local", "penales_visitante")
        return [dict(**{c: getattr(p, c) for c in campos},
                     equipo_local=equipos[p.equipo_local_id].nombre,
                     equipo_visitante=equipos[p.equipo_visitante_id].nombre,
                     fase=fases[p.fase_id].nombre, tipo_fase=fases[p.fase_id].tipo,
                     grupo=grupos.get(p.grupo_id)) for p in partidos]

    def obtener_fixture(self, id_torneo, equipo_id=None, fase_id=None):
        self.obtener_torneo(id_torneo)
        return self._vistas_partidos(self.repository.obtener_fixture(id_torneo, equipo_id, fase_id))

    def obtener_posiciones(self, id_torneo):
        """Recalcula desde resultados: corregir un marcador no duplica estadísticas."""
        self.obtener_torneo(id_torneo)
        grupos = self.repository.obtener_posiciones(id_torneo)
        inscripciones = self.repository.obtener_inscripciones(id_torneo)
        equipos = self.repository._equipos([i.equipo_id for i in inscripciones])
        partidos = self.repository.obtener_fixture(id_torneo)
        respuesta = []
        for grupo in grupos:
            miembros = [i for i in inscripciones if i.grupo_id == grupo.id]
            orden = {i.equipo_id: i.id for i in miembros}
            filas = {i.equipo_id: dict(equipo_id=i.equipo_id, equipo=equipos[i.equipo_id].nombre,
                     pj=0, pg=0, pe=0, pp=0, gf=0, gc=0, dg=0, puntos=0) for i in miembros}
            for p in partidos:
                if p.grupo_id != grupo.id or p.estado != "Finalizado":
                    continue
                for equipo_id, gf, gc in ((p.equipo_local_id, p.goles_local, p.goles_visitante),
                                          (p.equipo_visitante_id, p.goles_visitante, p.goles_local)):
                    fila = filas[equipo_id]
                    fila["pj"] += 1
                    fila["gf"] += gf
                    fila["gc"] += gc
                    fila["dg"] = fila["gf"] - fila["gc"]
                    fila["pg" if gf > gc else "pe" if gf == gc else "pp"] += 1
                    fila["puntos"] += 3 if gf > gc else 1 if gf == gc else 0
            # Último criterio explícito y estable: orden de inscripción.
            posiciones = sorted(filas.values(), key=lambda f: (-f["puntos"], -f["dg"], -f["gf"], orden[f["equipo_id"]]))
            for posicion, fila in enumerate(posiciones, 1):
                fila["posicion"] = posicion
            respuesta.append(dict(id=grupo.id, nombre=grupo.nombre, posiciones=posiciones))
        return respuesta

    @staticmethod
    def _ganador(partido):
        if partido.goles_local != partido.goles_visitante:
            return partido.equipo_local_id if partido.goles_local > partido.goles_visitante else partido.equipo_visitante_id
        return partido.equipo_local_id if partido.penales_local > partido.penales_visitante else partido.equipo_visitante_id

    @transaccion
    def avanzar_fase(self, id_torneo):
        """Genera una única ronda siguiente; los IDs se protegen además con restricciones únicas."""
        torneo = self.obtener_torneo(id_torneo, bloquear=True)
        self._exigir(torneo.estado == "En_Curso", "El campeonato no está en curso.")
        fases = self.repository.obtener_seguimiento(id_torneo)
        actual = fases[-1]
        previos = self.repository.obtener_fixture(id_torneo, fase_id=actual.id)
        self._exigir(bool(previos) and all(p.estado == "Finalizado" for p in previos),
                      "Todos los partidos de la fase actual deben tener resultado.")
        if actual.tipo == "Grupos":
            tablas = self.obtener_posiciones(id_torneo)
            # Orden por puesto y luego grupo: primeros contra últimos de otros grupos
            # cuando hay dos clasificados por grupo, sin sorteos ocultos.
            semillas = [g["posiciones"][puesto]["equipo_id"]
                        for puesto in range(torneo.clasifican_por_grupo) for g in tablas]
            parejas = [(semillas[i], semillas[-i - 1]) for i in range(len(semillas) // 2)]
        else:
            self._exigir(len(previos) > 1, "La final ya se disputó.")
            ganadores = [self._ganador(p) for p in sorted(previos, key=lambda p: p.numero)]
            parejas = list(zip(ganadores[::2], ganadores[1::2]))
        cantidad = len(parejas)
        nombre = {1: "Final", 2: "Semifinal", 4: "Cuartos de final", 8: "Octavos de final"}.get(cantidad, f"Ronda de {cantidad * 2}")
        fase = FaseModel(torneo_id=id_torneo, nombre=nombre, tipo="Eliminatoria_Directa", orden=actual.orden + 1)
        nuevos = [PartidoModel(torneo_id=id_torneo, numero=n, jornada=1,
                              equipo_local_id=local, equipo_visitante_id=visitante)
                  for n, (local, visitante) in enumerate(parejas, 1)]
        self.repository.avanzar_fase(fase, nuevos)
        return self.obtener_fixture(id_torneo, fase_id=fase.id)

    def _contexto_partido(self, id_partido):
        partido = self.repository._partido(id_partido)
        self._exigir(partido is not None, "Partido no existe.", 404)
        torneo = self.obtener_torneo(partido.torneo_id, bloquear=True)
        # Refresca después del bloqueo para no editar una versión desactualizada.
        self.repository.db.refresh(partido)
        fase = self.repository.db.get(FaseModel, partido.fase_id)
        fases = self.repository.obtener_seguimiento(torneo.id)
        self._exigir(fases[-1].id == fase.id, "Esta fase está cerrada: ya se generó la siguiente.")
        self._exigir(torneo.estado != "Cancelado", "El campeonato está cancelado.")
        return torneo, fase, partido

    @transaccion
    def programar_partido(self, id_partido, datos):
        torneo, fase, partido = self._contexto_partido(id_partido)
        self._exigir(partido.estado == "Programado", "No se puede reprogramar un partido finalizado.")
        self._exigir(torneo.fecha_inicio <= datos.fecha_hora.date() <= torneo.fecha_fin,
                      "La fecha debe estar dentro de las fechas del torneo.", 422)
        # Evita reservas exactas duplicadas de sede o equipos. La duración de
        # partidos no está definida aún, por lo que no se infieren intervalos.
        instante = datos.fecha_hora.astimezone(timezone.utc)
        conflicto = self.repository.db.query(PartidoModel).filter(
            PartidoModel.id != partido.id,
            PartidoModel.fecha_hora == instante,
            PartidoModel.estado == "Programado",
            or_(PartidoModel.sede == datos.sede,
                PartidoModel.equipo_local_id.in_([partido.equipo_local_id, partido.equipo_visitante_id]),
                PartidoModel.equipo_visitante_id.in_([partido.equipo_local_id, partido.equipo_visitante_id])),
        ).first()
        self._exigir(conflicto is None, "La sede o un equipo ya tiene otro partido a esa hora.")
        self.repository.programar_partido(partido, instante, datos.sede)
        return self._vistas_partidos([partido])[0]

    @transaccion
    def registrar_resultado(self, id_partido, datos):
        torneo, fase, partido = self._contexto_partido(id_partido)
        if fase.tipo == "Grupos":
            self._exigir(datos.penales_local is None, "Los grupos no usan penales.", 422)
        elif datos.goles_local == datos.goles_visitante:
            self._exigir(datos.penales_local is not None and datos.penales_local != datos.penales_visitante,
                          "Un empate eliminatorio requiere penales con ganador.", 422)
        else:
            self._exigir(datos.penales_local is None, "No se requieren penales si no hay empate.", 422)
        self.repository.registrar_resultado(partido, datos)
        if fase.tipo == "Eliminatoria_Directa" and len(self.repository.obtener_fixture(torneo.id, fase_id=fase.id)) == 1:
            torneo.estado = "Finalizado"
        return self._vistas_partidos([partido])[0]

    def obtener_seguimiento(self, id_torneo):
        torneo = self.obtener_torneo(id_torneo)
        fases = self.repository.obtener_seguimiento(id_torneo)
        partidos = self.repository.obtener_fixture(id_torneo)
        terminados = sum(p.estado == "Finalizado" for p in partidos)
        campeon_id = None
        if torneo.estado == "Finalizado" and fases:
            final = next(p for p in partidos if p.fase_id == fases[-1].id)
            campeon_id = self._ganador(final)
        campeon = self.repository._equipos([campeon_id]).get(campeon_id) if campeon_id else None
        return dict(torneo=torneo, equipos_inscritos=len(self.repository.obtener_inscripciones(id_torneo)),
                    partidos_generados=len(partidos), partidos_finalizados=terminados,
                    partidos_pendientes=len(partidos) - terminados,
                    fase_actual=fases[-1].nombre if fases else None,
                    campeon_id=campeon_id, campeon=campeon.nombre if campeon else None,
                    porcentaje_fixture_completado=round(100 * terminados / len(partidos), 2) if partidos else 0)
