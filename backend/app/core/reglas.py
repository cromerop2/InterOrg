"""Reglas configurables de un torneo (campo `reglas`) con valores por defecto."""

MINIMO_JUGADORES = 11  # reglas["min_jugadores"]
MAXIMO_JUGADORES = 25  # reglas["max_jugadores"]
MINIMO_EQUIPOS = 2  # reglas["min_equipos"]: equipos Habilitados para poder iniciar el torneo
TITULARES = 11  # reglas["titulares"]: jugadores que arrancan en una alineación
MAXIMO_SUPLENTES = 7  # reglas["max_suplentes"]
DURACION_PARTIDO_MIN = 90  # reglas["duracion_partido_min"]: se usa para evitar cruces de horario
MAXIMO_SUSTITUCIONES = 5  # reglas["max_sustituciones"]: cambios permitidos por equipo y partido
PUNTOS_VICTORIA = 3  # reglas["puntos_victoria"]
PUNTOS_EMPATE = 1  # reglas["puntos_empate"]
GOLES_WALKOVER = 3  # reglas["goles_walkover"]: marcador a favor de quien se presenta (3-0)
CLASIFICAN_POR_GRUPO = 2  # reglas["clasifican_por_grupo"]
FECHAS_POR_ROJA = 1  # reglas["fechas_por_roja"]: fechas de suspensión automática tras una tarjeta roja


def obtener_regla_entera(torneo, clave: str, defecto: int) -> int:
    """Lee un número de torneo.reglas; si falta o no es un entero válido, usa el valor por defecto."""
    reglas = torneo.reglas if isinstance(torneo.reglas, dict) else {}
    valor = reglas.get(clave, defecto)
    if isinstance(valor, bool) or not isinstance(valor, int) or valor < 0:
        return defecto
    return valor


def permite_transferencias(torneo) -> bool:
    """reglas["permite_transferencias"] debe ser exactamente true."""
    reglas = torneo.reglas if isinstance(torneo.reglas, dict) else {}
    return reglas.get("permite_transferencias") is True
