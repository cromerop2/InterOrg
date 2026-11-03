/** Contratos de la API; los resultados y las posiciones se calculan en el backend. */
export type Tournament = { id:number; nombre:string; categoria:string; estado:string; fecha_inicio:string; fecha_fin:string; numero_grupos:number; clasifican_por_grupo:number };
export type Team = { id:number; nombre:string; colegio_id:number; entrenador_id:number };
export type User = { id:number; nombre_completo:string; rol:string; email:string };
export type College = { id:number; nombre:string };
export type Entry = { id:number; equipo_id:number; grupo_id:number|null };
export type Player = { id:number; nombre_completo:string; numero_camiseta:number|null };
export type Match = {
  id:number; fase_id:number; fase:string; tipo_fase:string; grupo:string|null; grupo_id:number|null;
  equipo_local_id:number; equipo_visitante_id:number; equipo_local:string; equipo_visitante:string;
  jornada:number; estado:string; fecha_hora:string|null; sede:string|null;
  goles_local:number|null; goles_visitante:number|null; penales_local:number|null; penales_visitante:number|null;
};
export type Row = { equipo_id:number; equipo:string; posicion:number; pj:number; pg:number; pe:number; pp:number; gf:number; gc:number; dg:number; puntos:number };
export type Group = { id:number; nombre:string; posiciones:Row[]; criterio_desempate:string };
export type Progress = { torneo:Tournament; fase_actual:string|null; campeon:string|null; equipos_inscritos:number; partidos_finalizados:number; partidos_pendientes:number; porcentaje_fixture_completado:number };
