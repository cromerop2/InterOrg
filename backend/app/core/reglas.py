"""Reglas configurables de un torneo (campo `reglas`) con valores por defecto."""

MINIMO_JUGADORES = 11  # reglas["min_jugadores"]
MAXIMO_JUGADORES = 25  # reglas["max_jugadores"]
MINIMO_EQUIPOS = 2  # reglas["min_equipos"]: equipos Habilitados para poder iniciar el torneo


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
