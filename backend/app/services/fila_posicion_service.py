"""Cálculo de las estadísticas de un equipo dentro de un grupo."""

from fastapi import HTTPException, status

from app.core.reglas import PUNTOS_EMPATE, PUNTOS_VICTORIA
from app.models.fila_posicion_model import FilaPosicionModel
from app.repositories.fila_posicion_repository import FilaPosicionRepository


class FilaPosicionService:
    def __init__(self, repository: FilaPosicionRepository):
        self.repository = repository

    def procesar_resultado_partido(
        self,
        id_tabla: int,
        id_equipo: int,
        goles_propios: int,
        goles_rivales: int,
        puntos_victoria: int = PUNTOS_VICTORIA,
        puntos_empate: int = PUNTOS_EMPATE,
        confirmar: bool = True,
    ) -> FilaPosicionModel:
        """Suma el resultado de un partido a las estadísticas del equipo."""
        return self._aplicar(+1, id_tabla, id_equipo, goles_propios, goles_rivales, puntos_victoria, puntos_empate, confirmar)

    def revertir_resultado_partido(
        self,
        id_tabla: int,
        id_equipo: int,
        goles_propios: int,
        goles_rivales: int,
        puntos_victoria: int = PUNTOS_VICTORIA,
        puntos_empate: int = PUNTOS_EMPATE,
        confirmar: bool = True,
    ) -> FilaPosicionModel:
        """Resta un resultado ya sumado. Se usa antes de aplicar uno corregido (ej. W.O. por alineación indebida),
        para que la tabla no se corrompa."""
        return self._aplicar(-1, id_tabla, id_equipo, goles_propios, goles_rivales, puntos_victoria, puntos_empate, confirmar)

    def _aplicar(self, signo, id_tabla, id_equipo, goles_propios, goles_rivales, puntos_victoria, puntos_empate, confirmar):
        fila = self.repository.obtener_por_tabla_y_equipo(id_tabla, id_equipo)
        if fila is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "El equipo no está en esa tabla de posiciones.")

        ganados, empatados, perdidos, puntos = fila.partidos_ganados, fila.partidos_empatados, fila.partidos_perdidos, fila.puntos
        if goles_propios > goles_rivales:
            ganados += signo
            puntos += signo * puntos_victoria
        elif goles_propios == goles_rivales:
            empatados += signo
            puntos += signo * puntos_empate
        else:
            perdidos += signo

        a_favor = fila.goles_a_favor + signo * goles_propios
        en_contra = fila.goles_en_contra + signo * goles_rivales
        metricas = {
            "partidos_jugados": fila.partidos_jugados + signo,
            "partidos_ganados": ganados,
            "partidos_empatados": empatados,
            "partidos_perdidos": perdidos,
            "goles_a_favor": a_favor,
            "goles_en_contra": en_contra,
            "diferencia_goles": a_favor - en_contra,
            "puntos": puntos,
        }
        return self.repository.actualizar_metricas(fila, metricas, confirmar)
