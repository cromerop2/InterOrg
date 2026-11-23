"""Valida los datos de grupos y tablas de posiciones."""

from pydantic import BaseModel, ConfigDict, Field, model_validator


class GruposConfiguracion(BaseModel):
    """Reparto de equipos por grupo, ej. {"Grupo A": [1, 2, 3], "Grupo B": [4, 5]}."""

    model_config = ConfigDict(extra="forbid")

    grupos: dict[str, list[int]]

    @model_validator(mode="after")
    def validar_reparto(self) -> "GruposConfiguracion":
        if not 1 <= len(self.grupos) <= 16:
            raise ValueError("Debe haber entre 1 y 16 grupos.")
        vistos: set[int] = set()
        for nombre, equipos in self.grupos.items():
            if not nombre.strip():
                raise ValueError("El nombre de un grupo no puede estar vacío.")
            if len(equipos) < 2:
                raise ValueError(f"El grupo '{nombre}' necesita al menos 2 equipos.")
            if any(id_equipo <= 0 for id_equipo in equipos):
                raise ValueError("Los ids de equipo deben ser positivos.")
            if len(set(equipos)) != len(equipos):
                raise ValueError(f"El grupo '{nombre}' repite equipos.")
            if vistos & set(equipos):
                raise ValueError("Un equipo no puede estar en dos grupos.")
            vistos |= set(equipos)
        return self


class FilaPosicionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tabla_id: int
    equipo_id: int
    partidos_jugados: int = Field(description="PJ")
    partidos_ganados: int = Field(description="PG")
    partidos_empatados: int = Field(description="PE")
    partidos_perdidos: int = Field(description="PP")
    goles_a_favor: int = Field(description="GF")
    goles_en_contra: int = Field(description="GC")
    diferencia_goles: int = Field(description="DG")
    puntos: int = Field(description="PTS")


class TablaPosicionesResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fase_id: int
    nombre_grupo: str
    estado_cierre: bool


class TablaClasificacionResponse(TablaPosicionesResponse):
    """La tabla con sus filas ya ordenadas por posición."""

    filas: list[FilaPosicionResponse]


class CierreGrupoResponse(TablaClasificacionResponse):
    """El grupo ya cerrado y los equipos que clasifican, en orden de posición."""

    clasificados: list[int]
