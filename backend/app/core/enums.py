import enum

class RolEnum(str, enum.Enum):
    ADMINISTRADOR = "Administrador"
    ENTRENADOR = "Entrenador"
    ARBITRO = "Arbitro"

class EstadoTorneoEnum(str, enum.Enum):
    INSCRIPCIONES = "Inscripciones"
    EN_CURSO = "En_Curso"
    FINALIZADO = "Finalizado"
    CANCELADO = "Cancelado"

class TipoFormatoEnum(str, enum.Enum):
    GRUPOS = "Grupos"
    ELIMINATORIA_DIRECTA = "Eliminatoria_Directa"

class EstadoFaseEnum(str, enum.Enum):
    PROGRAMADA = "Programada"
    EN_JUEGO = "En_Juego"
    FINALIZADA = "Finalizada"

class EstadoInscripcionEnum(str, enum.Enum):
    PENDIENTE = "Pendiente"
    HABILITADO = "Habilitado"
    RECHAZADO = "Rechazado"

class EstadoPagoEnum(str, enum.Enum):
    PENDIENTE = "Pendiente"
    APROBADO = "Aprobado"
    RECHAZADO = "Rechazado"

class EstadoPartidoEnum(str, enum.Enum):
    PROGRAMADO = "Programado"
    EN_JUEGO = "En_Juego"
    FINALIZADO = "Finalizado"
    SUSPENDIDO = "Suspendido"
    W_O = "W_O"

class TipoEventoEnum(str, enum.Enum):
    GOL = "Gol"
    ASISTENCIA = "Asistencia"
    TARJETA_AMARILLA = "Tarjeta_Amarilla"
    TARJETA_ROJA = "Tarjeta_Roja"
    SUSTITUCION = "Sustitucion"
    AUTOGOL = "Autogol"