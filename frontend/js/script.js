/* ============================================================
   Copa Intercolegiada — frontend conectado a la API (FastAPI)
   Sin datos de ejemplo: todo viene de fetch(). La API se sirve en el
   mismo origen (backend/app/main.py monta esta carpeta en "/"). Para
   usar otra dirección define window.API_BASE antes de cargar este script.
   ============================================================ */
const API_BASE = window.API_BASE || "";

/* ---------- 1. CONSTANTES ---------- */
const EVENT_META = {
  Gol: { label: "Gol", icon: "⚽", bg: "bg-emerald-50" },
  Autogol: { label: "Autogol", icon: "⚽", bg: "bg-slate-50" },
  Asistencia: { label: "Asistencia", icon: "👟", bg: "bg-blue-50" },
  Tarjeta_Amarilla: { label: "Tarjeta amarilla", icon: "🟨", bg: "bg-amber-50" },
  Tarjeta_Roja: { label: "Tarjeta roja", icon: "🟥", bg: "bg-red-50" },
  Sustitucion: { label: "Sustitución", icon: "🔁", bg: "bg-blue-50" },
};
const POSICIONES = ["Portero", "Defensa", "Mediocampo", "Delantero"];
const POSICION_COLOR = {
  Portero: "bg-purple-100 text-purple-700", Defensa: "bg-blue-100 text-blue-700",
  Mediocampo: "bg-amber-100 text-amber-700", Delantero: "bg-emerald-100 text-emerald-700",
};
const ADMIN_SECTIONS = [
  { id: "TORNEOS", label: "Torneos y Fases" },
  { id: "FIXTURES", label: "Fixtures y Partidos" },
  { id: "SEDES", label: "Sedes y Canchas" },
  { id: "INSTITUCIONES", label: "Colegios, Equipos y Pagos" },
  { id: "USUARIOS", label: "Cuentas de usuario" },
];
const SUPERFICIES = ["Sintética", "Grama", "Cemento", "Coliseo"];
const NAV_ITEMS = [
  { id: "DASHBOARD_PUBLICO", label: "Dashboard Público", icon: "trophy" },
  { id: "PLANILLA_ARBITRO", label: "Planilla Árbitro", icon: "clipboard-list" },
  { id: "PANEL_COACH", label: "Panel Entrenador", icon: "shield-check" },
  { id: "PANEL_ADMIN", label: "Panel Admin", icon: "settings-2" },
];
const ROL_DE_VISTA = { PLANILLA_ARBITRO: "Arbitro", PANEL_COACH: "Entrenador", PANEL_ADMIN: "Administrador" };
const INPUT = "w-full border border-slate-200 rounded-lg px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-emerald-600";
const BTN = "bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold px-4 py-2 rounded-lg disabled:opacity-40";

/* ---------- 2. SESIÓN Y API ---------- */
const memoria = {};
const almacen = {
  get(k) { try { return sessionStorage.getItem(k) ?? memoria[k] ?? null; } catch { return memoria[k] ?? null; } },
  set(k, v) { memoria[k] = v; try { sessionStorage.setItem(k, v); } catch { /* sin almacenamiento */ } },
  del(k) { delete memoria[k]; try { sessionStorage.removeItem(k); } catch { /* sin almacenamiento */ } },
};

class ApiError extends Error { constructor(status, message) { super(message); this.status = status; } }

function mensajeDeError(datos, status) {
  const d = datos && datos.detail;
  if (typeof d === "string") return d;
  if (Array.isArray(d)) return d.map((e) => `${(e.loc || []).slice(1).join(".")}: ${e.msg}`).join(" · ");
  return `Error ${status}`;
}

async function api(metodo, ruta, cuerpo) {
  const headers = {};
  if (cuerpo !== undefined) headers["Content-Type"] = "application/json";
  if (state.session) headers.Authorization = "Bearer " + state.session.token;
  let r;
  try {
    r = await fetch(API_BASE + ruta, { method: metodo, headers, body: cuerpo !== undefined ? JSON.stringify(cuerpo) : undefined });
  } catch {
    throw new ApiError(0, "No se pudo conectar con la API. ¿Está encendido el servidor?");
  }
  if (r.status === 204) return null;
  let datos = null;
  try { datos = await r.json(); } catch { /* sin cuerpo */ }
  if (!r.ok) {
    if (r.status === 401 && state.session) cerrarSesion("Tu sesión expiró. Inicia sesión de nuevo.");
    throw new ApiError(r.status, mensajeDeError(datos, r.status));
  }
  return datos;
}
const GET = (ruta) => api("GET", ruta);
const POST = (ruta, cuerpo) => api("POST", ruta, cuerpo === undefined ? {} : cuerpo);
const PUT = (ruta, cuerpo) => api("PUT", ruta, cuerpo);
const PATCH = (ruta, cuerpo) => api("PATCH", ruta, cuerpo);
const DELETE = (ruta) => api("DELETE", ruta);

/** Ejecuta una acción y muestra el error de la API como aviso, sin romper la pantalla. */
async function intentar(fn) {
  try { return await fn(); } catch (e) { if (e instanceof ApiError) mostrarToast(e.message, "error"); else { console.error(e); mostrarToast("Ocurrió un error inesperado.", "error"); } }
}

/* ---------- 3. ESTADO ---------- */
const state = {
  view: "DASHBOARD_PUBLICO",
  session: null, loginModal: false, cargando: false, error: null,
  nombres: {}, // id de equipo -> nombre
  dash: { torneos: [], torneoId: null, fases: [], faseId: null, tablas: [], partidos: [], goleadores: [], destacado: null, marcador: null, tab: "POSICIONES", timer: null },
  arb: { partidos: [], id: null, marcador: null, alin: [], eventos: [], seconds: 0, running: false, timerId: null, modal: null },
  coach: { equipos: [], colegios: [], torneos: [], equipoId: null, jugadores: [], calendario: [], showPago: false, showEquipo: false, planilla: null },
  admin: { section: "TORNEOS", torneos: [], torneoId: null, fases: [], faseId: null, partidos: [], tablas: [], equipos: [], canchas: [], colegios: [], usuarios: [], pagos: [] },
  toast: null, toastTimer: null,
};
try {
  const t = almacen.get("token"), rol = almacen.get("rol"), nombre = almacen.get("nombre");
  if (t && rol) state.session = { token: t, rol, nombre: nombre || "" };
} catch { /* sin sesión */ }

/* ---------- 4. HELPERS ---------- */
function esc(s) { return String(s ?? "").replace(/[&<>"']/g, (m) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[m])); }
const nombreEquipo = (id) => state.nombres[id] || `Equipo #${id}`;
const fechaDe = (iso) => String(iso || "").slice(0, 10);
const horaDe = (iso) => String(iso || "").slice(11, 16);
const porId = (lista, id) => lista.find((x) => String(x.id) === String(id));
function siglaDe(nombre) { return String(nombre).split(/\s+/).filter(Boolean).map((p) => p[0]).join("").slice(0, 3).toUpperCase() || "?"; }
async function cargarNombres(idTorneo) {
  const equipos = await GET(`/torneos/${idTorneo}/equipos/publico`);
  equipos.forEach((e) => { state.nombres[e.id] = e.nombre; });
}

function mostrarToast(message, type) {
  state.toast = { message, type: type || "success" };
  renderToast();
  clearTimeout(state.toastTimer);
  state.toastTimer = setTimeout(() => { state.toast = null; renderToast(); }, 4000);
}
function renderToast() {
  const t = state.toast;
  const styles = { success: "bg-emerald-600", error: "bg-red-600", info: "bg-blue-950" };
  document.getElementById("toast-root").innerHTML = t ? `
  <div class="fixed top-4 left-1/2 -translate-x-1/2 z-[60] px-4 max-w-full">
    <div class="flex items-center gap-2 text-white text-xs font-semibold px-4 py-2.5 rounded-lg shadow-lg ${styles[t.type] || styles.success}">${esc(t.message)}</div>
  </div>` : "";
}

function filterDropdown(valor, opciones, etiqueta, accion, extra) {
  return `
  <div class="relative">
    <select data-action="${accion}" ${extra || ""} class="appearance-none bg-white border border-slate-200 rounded-lg pl-3 pr-8 py-2 text-xs font-medium text-blue-900 shadow-sm cursor-pointer focus:outline-none focus:ring-2 focus:ring-emerald-600">
      ${opciones.map((o) => `<option value="${esc(o.value)}" ${String(o.value) === String(valor) ? "selected" : ""}>${esc(o.label)}</option>`).join("")}
    </select>
    <i data-lucide="chevron-down" class="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 w-3.5 h-3.5"></i>
  </div>`;
}
const vacio = (texto) => `<div class="min-h-[60vh] flex items-center justify-center px-6 text-center"><p class="text-sm text-slate-400">${esc(texto)}</p></div>`;
const campo = (etiqueta, html) => `<div><label class="text-[11px] font-semibold text-slate-500 mb-1 block">${etiqueta}</label>${html}</div>`;
const entrada = (name, ph, extra) => `<input name="${name}" placeholder="${esc(ph || "")}" ${extra || ""} class="${INPUT}">`;

/* ---------- 5. RENDER RAÍZ ---------- */
function render() {
  document.getElementById("header").innerHTML = renderHeader();
  const main = document.getElementById("main");
  const rol = ROL_DE_VISTA[state.view];
  if (rol && (!state.session || state.session.rol !== rol)) main.innerHTML = panelDeAcceso(rol);
  else if (state.cargando) main.innerHTML = vacio("Cargando…");
  else if (state.error) main.innerHTML = vacio(state.error);
  else if (state.view === "DASHBOARD_PUBLICO") main.innerHTML = renderDashboard();
  else if (state.view === "PLANILLA_ARBITRO") main.innerHTML = renderArbitro();
  else if (state.view === "PANEL_COACH") main.innerHTML = renderCoach();
  else if (state.view === "PANEL_ADMIN") main.innerHTML = renderAdmin();
  document.getElementById("modal-root") || document.body.insertAdjacentHTML("beforeend", '<div id="modal-root"></div>');
  document.getElementById("modal-root").innerHTML = state.loginModal ? loginModalHTML() : "";
  if (window.lucide) lucide.createIcons();
}

async function setView(v) {
  detenerRelojes();
  state.view = v; state.error = null;
  await cargarVista();
}
async function cargarVista() {
  const rol = ROL_DE_VISTA[state.view];
  if (rol && (!state.session || state.session.rol !== rol)) { render(); return; }
  state.cargando = true; render();
  try {
    if (state.view === "DASHBOARD_PUBLICO") await cargarDashboard();
    else if (state.view === "PLANILLA_ARBITRO") await cargarArbitro();
    else if (state.view === "PANEL_COACH") await cargarCoach();
    else if (state.view === "PANEL_ADMIN") await cargarAdmin();
  } catch (e) { state.error = e instanceof ApiError ? e.message : "No se pudo cargar la pantalla."; if (!(e instanceof ApiError)) console.error(e); }
  state.cargando = false; render();
}
function detenerRelojes() {
  clearInterval(state.arb.timerId); state.arb.running = false;
  clearInterval(state.dash.timer); state.dash.timer = null;
}

/* ---------- 6. HEADER, LOGIN ---------- */
function renderHeader() {
  const s = state.session;
  return `
  <header class="sticky top-0 z-40 bg-blue-950 shadow-sm">
    <div class="mx-auto max-w-6xl px-4 py-3 flex items-center justify-between gap-4 flex-wrap">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-lg bg-emerald-600 flex items-center justify-center text-white font-bold text-sm">CI</div>
        <div class="leading-tight"><p class="text-white font-semibold text-sm">Copa Intercolegiada 2026</p><p class="text-blue-200/70 text-xs">Cartagena · Torneo Intercolegiado</p></div>
      </div>
      <nav class="flex items-center gap-1 overflow-x-auto">
        ${NAV_ITEMS.map((n) => `<button data-nav="${n.id}" class="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium whitespace-nowrap transition-colors ${state.view === n.id ? "bg-white text-blue-950" : "text-blue-200/80 hover:bg-white/10 hover:text-white"}"><i data-lucide="${n.icon}" class="w-3.5 h-3.5"></i>${n.label}</button>`).join("")}
        ${s ? `<span class="text-[11px] text-blue-200/80 px-2 whitespace-nowrap">${esc(s.nombre || s.rol)} · ${esc(s.rol)}</span><button data-action="cerrar-sesion" class="text-[11px] font-semibold text-white bg-white/10 hover:bg-white/20 px-3 py-2 rounded-lg">Salir</button>`
              : `<button data-action="abrir-login" class="text-[11px] font-semibold text-white bg-emerald-600 hover:bg-emerald-700 px-3 py-2 rounded-lg">Iniciar sesión</button>`}
      </nav>
    </div>
  </header>`;
}
function panelDeAcceso(rol) {
  const otra = state.session ? `Tu sesión es de ${esc(state.session.rol)}. ` : "";
  return `<div class="min-h-[60vh] flex items-center justify-center px-6"><div class="bg-white rounded-xl shadow-sm p-6 max-w-sm text-center">
    <p class="text-sm font-bold text-blue-950 mb-1">Esta pantalla es para ${esc(rol)}</p>
    <p class="text-xs text-slate-500 mb-4">${otra}Inicia sesión con una cuenta de ${esc(rol)} para continuar.</p>
    <button data-action="abrir-login" class="${BTN}">Iniciar sesión</button></div></div>`;
}
function loginModalHTML() {
  return `
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4">
    <form id="form-login" class="bg-white rounded-2xl p-5 max-w-sm w-full">
      <p class="text-sm font-bold text-blue-950 mb-3">Iniciar sesión</p>
      <div class="flex flex-col gap-3">
        ${campo("Correo", entrada("email", "correo@colegio.edu.co", 'type="email" required autocomplete="username"'))}
        ${campo("Contraseña", entrada("password", "", 'type="password" required autocomplete="current-password"'))}
      </div>
      <div class="flex justify-end gap-2 mt-4">
        <button type="button" data-action="cerrar-login" class="text-xs font-semibold text-slate-500 px-3 py-2 rounded-lg hover:bg-slate-50">Cancelar</button>
        <button type="submit" class="${BTN}">Entrar</button>
      </div>
    </form>
  </div>`;
}
async function iniciarSesion(email, password) {
  const t = await api("POST", "/auth/login", { email, password });
  state.session = { token: t.access_token, rol: t.rol, nombre: "" };
  const yo = await GET("/auth/me");
  state.session.nombre = yo.nombre_completo;
  almacen.set("token", t.access_token); almacen.set("rol", t.rol); almacen.set("nombre", yo.nombre_completo);
  state.loginModal = false;
  mostrarToast(`Bienvenido, ${yo.nombre_completo}.`);
  const vistaDelRol = Object.keys(ROL_DE_VISTA).find((k) => ROL_DE_VISTA[k] === t.rol);
  if (ROL_DE_VISTA[state.view] !== t.rol && vistaDelRol && state.view !== "DASHBOARD_PUBLICO") state.view = vistaDelRol;
  await cargarVista();
}
function cerrarSesion(aviso) {
  detenerRelojes();
  state.session = null;
  ["token", "rol", "nombre"].forEach((k) => almacen.del(k));
  if (aviso) mostrarToast(typeof aviso === "string" ? aviso : "Sesión cerrada.", "info");
  state.arb = { ...state.arb, partidos: [], id: null, marcador: null, alin: [], eventos: [], seconds: 0, modal: null };
  state.coach = { ...state.coach, equipos: [], equipoId: null, jugadores: [], calendario: [], planilla: null };
  render();
}

/* ============================================================
   7. PANTALLA 1 — DASHBOARD PÚBLICO (sin sesión)
   ============================================================ */
async function cargarDashboard() {
  const d = state.dash;
  d.torneos = await GET("/torneos/");
  if (!d.torneos.length) { d.fases = []; d.tablas = []; d.partidos = []; d.goleadores = []; d.destacado = null; return; }
  if (!porId(d.torneos, d.torneoId)) d.torneoId = (d.torneos.find((t) => t.estado === "En_Curso") || d.torneos[0]).id;
  d.fases = await GET(`/torneos/${d.torneoId}/fases`);
  if (!porId(d.fases, d.faseId)) d.faseId = (d.fases.find((f) => f.estado === "En_Juego") || d.fases.find((f) => f.estado === "Programada") || d.fases[d.fases.length - 1] || {}).id ?? null;
  await refrescarDashboard();
  if (!d.timer) d.timer = setInterval(async () => { if (state.view !== "DASHBOARD_PUBLICO" || state.loginModal) return; try { await refrescarDashboard(); render(); } catch { /* reintenta luego */ } }, 15000);
}
async function refrescarDashboard() {
  const d = state.dash;
  await cargarNombres(d.torneoId);
  d.goleadores = await GET(`/torneos/${d.torneoId}/goleadores?limite=5`);
  if (d.faseId == null) { d.tablas = []; d.partidos = []; d.destacado = null; return; }
  [d.tablas, d.partidos] = await Promise.all([GET(`/fases/${d.faseId}/tablas`), GET(`/fases/${d.faseId}/partidos`)]);
  const orden = [...d.partidos].sort((a, b) => a.fecha_hora.localeCompare(b.fecha_hora));
  d.destacado = orden.find((p) => p.estado === "En_Juego") || orden.find((p) => p.estado === "Programado") || orden[orden.length - 1] || null;
  d.marcador = d.destacado ? await GET(`/partidos/${d.destacado.id}/marcador`) : null;
}

function renderDashboard() {
  const d = state.dash;
  if (!d.torneos.length) return vacio("Todavía no hay torneos publicados.");
  const proximos = d.partidos.filter((p) => p.estado === "Programado").sort((a, b) => a.fecha_hora.localeCompare(b.fecha_hora));
  return `
  <div class="min-h-screen bg-slate-50">
    <div class="mx-auto max-w-6xl px-4 pt-6 flex flex-wrap gap-3">
      ${filterDropdown(d.torneoId, d.torneos.map((t) => ({ value: t.id, label: `${t.nombre} · ${t.categoria}` })), null, "dash-torneo")}
      ${d.fases.length ? filterDropdown(d.faseId, d.fases.map((f) => ({ value: f.id, label: "Fase: " + f.nombre })), null, "dash-fase") : ""}
    </div>
    <div class="mx-auto max-w-6xl px-4 py-6 grid grid-cols-1 lg:grid-cols-[2fr_1fr] gap-6 items-start">
      <div class="flex flex-col gap-6">
        ${d.destacado ? partidoDestacadoCard(d.destacado, d.marcador) : ""}
        <div class="bg-white rounded-xl shadow-sm overflow-hidden">
          <div class="flex border-b border-slate-100">
            ${["POSICIONES", "GOLEADORES"].map((t) => `<button data-action="dashboard-tab" data-tab="${t}" class="flex-1 py-3 text-xs font-semibold transition-colors ${d.tab === t ? "text-emerald-700 border-b-2 border-emerald-600 bg-emerald-50/50" : "text-slate-400 hover:text-slate-600"}">${t === "POSICIONES" ? "Tabla General" : "Líderes de Goleo"}</button>`).join("")}
          </div>
          ${d.tab === "POSICIONES" ? tablasPosicionesHTML() : tablaGoleadoresHTML()}
        </div>
      </div>
      <aside class="bg-white rounded-xl shadow-sm p-4">
        <h3 class="text-sm font-semibold text-blue-950 mb-3">Próximos partidos</h3>
        <div class="flex flex-col gap-3">
          ${proximos.length === 0 ? `<p class="text-xs text-slate-400">No hay partidos programados.</p>` : ""}
          ${proximos.map((p) => `
            <div class="flex items-center gap-2 text-xs text-slate-600"><i data-lucide="clock" class="w-3.5 h-3.5 text-slate-400 shrink-0"></i>
              <span class="flex-1">${esc(nombreEquipo(p.equipo_local_id))} vs ${esc(nombreEquipo(p.equipo_visitante_id))}</span>
              <span class="text-slate-400 text-right">${esc(fechaDe(p.fecha_hora))}<br>${esc(horaDe(p.fecha_hora))}</span></div>`).join("")}
        </div>
      </aside>
    </div>
  </div>`;
}

function partidoDestacadoCard(p, m) {
  const enVivo = p.estado === "En_Juego", final = p.estado === "Finalizado" || p.estado === "W_O";
  const etiqueta = enVivo ? "EN VIVO" : final ? (p.estado === "W_O" ? "W.O." : "FINALIZADO") : "PRÓXIMO PARTIDO";
  const verMarcador = enVivo || final;
  const escudo = (id) => `<div class="w-12 h-12 mx-auto mb-2 rounded-lg bg-white/10 flex items-center justify-center text-sm font-bold">${esc(siglaDe(nombreEquipo(id)))}</div>`;
  return `
  <div class="rounded-xl bg-blue-950 text-white p-5 shadow-sm">
    <div class="inline-flex items-center gap-2 ${enVivo ? "bg-emerald-600" : "bg-white/10 text-blue-100"} text-[11px] font-bold px-3 py-1 rounded-full mb-4">
      ${enVivo ? `<span class="relative flex h-2 w-2"><span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-white/80 opacity-75"></span><span class="relative inline-flex rounded-full h-2 w-2 bg-white"></span></span>` : ""}${etiqueta}
    </div>
    <div class="flex items-center justify-between gap-4">
      <div class="flex-1 text-center">${escudo(p.equipo_local_id)}<p class="text-xs font-semibold leading-tight">${esc(nombreEquipo(p.equipo_local_id))}</p></div>
      <div class="px-3 text-2xl font-extrabold tabular-nums">${verMarcador && m ? m.goles_local : "-"}&nbsp;–&nbsp;${verMarcador && m ? m.goles_visitante : "-"}</div>
      <div class="flex-1 text-center">${escudo(p.equipo_visitante_id)}<p class="text-xs font-semibold leading-tight">${esc(nombreEquipo(p.equipo_visitante_id))}</p></div>
    </div>
    ${verMarcador && m && m.goles_penales_local != null ? `<p class="text-center text-[11px] text-blue-200/80 mt-2">Penales ${m.goles_penales_local} – ${m.goles_penales_visitante}</p>` : ""}
    <div class="flex items-center justify-center gap-4 mt-4 text-[11px] text-blue-200/70">
      <span class="flex items-center gap-1"><i data-lucide="map-pin" class="w-3 h-3"></i>Cancha ${p.cancha_id}</span>
      <span class="flex items-center gap-1"><i data-lucide="clock" class="w-3 h-3"></i>${esc(fechaDe(p.fecha_hora))} ${esc(horaDe(p.fecha_hora))}</span>
    </div>
  </div>`;
}

const TH = (t, c) => `<th class="py-2.5 px-${c || 2} text-center font-medium">${t}</th>`;
function tablasPosicionesHTML() {
  const d = state.dash;
  if (!d.tablas.length) {
    const fase = porId(d.fases, d.faseId);
    return `<p class="py-8 text-center text-xs text-slate-400">${fase && fase.tipo_formato === "Eliminatoria_Directa" ? "La eliminatoria directa no tiene tabla de posiciones." : "Aún no hay grupos definidos para esta fase."}</p>`;
  }
  return d.tablas.map((t) => `
  <div class="overflow-x-auto">
    <p class="px-4 pt-3 text-[11px] font-bold text-blue-950 uppercase tracking-wide">${esc(t.nombre_grupo)} ${t.estado_cierre ? "· cerrado" : ""}</p>
    <table class="w-full text-xs"><thead><tr class="text-slate-400 border-b border-slate-100">
      ${TH("POS", 3)}<th class="py-2.5 px-3 text-left font-medium">EQUIPO</th>${["PJ", "PG", "PE", "PP", "GF", "GC", "DG"].map((x) => TH(x)).join("")}${TH("PTS", 3)}
    </tr></thead><tbody>
      ${t.filas.map((f, i) => { const clas = i < 2; return `
      <tr class="border-b border-slate-50 last:border-0 ${clas ? "bg-emerald-50/60" : ""}">
        <td class="py-2.5 px-3 text-center"><span class="inline-flex items-center justify-center w-5 h-5 rounded text-[11px] font-bold ${clas ? "bg-emerald-600 text-white" : "bg-slate-100 text-slate-500"}">${i + 1}</span></td>
        <td class="py-2.5 px-3"><div class="flex items-center gap-2"><div class="w-6 h-6 rounded bg-blue-950 text-white flex items-center justify-center text-[9px] font-bold shrink-0">${esc(siglaDe(nombreEquipo(f.equipo_id)))}</div><span class="font-medium text-slate-700">${esc(nombreEquipo(f.equipo_id))}</span></div></td>
        ${[f.partidos_jugados, f.partidos_ganados, f.partidos_empatados, f.partidos_perdidos, f.goles_a_favor, f.goles_en_contra].map((v) => `<td class="py-2.5 px-2 text-center text-slate-600">${v}</td>`).join("")}
        <td class="py-2.5 px-2 text-center text-slate-600 tabular-nums">${f.diferencia_goles > 0 ? "+" + f.diferencia_goles : f.diferencia_goles}</td>
        <td class="py-2.5 px-3 text-center font-bold text-blue-900">${f.puntos}</td></tr>`; }).join("")}
    </tbody></table></div>`).join("");
}
function tablaGoleadoresHTML() {
  const g = state.dash.goleadores;
  return `<div class="overflow-x-auto"><table class="w-full text-xs"><thead><tr class="text-slate-400 border-b border-slate-100">
    ${TH("POS", 3)}<th class="py-2.5 px-3 text-left font-medium">JUGADOR</th><th class="py-2.5 px-3 text-left font-medium">EQUIPO</th>${TH("GOLES", 3)}</tr></thead><tbody>
    ${g.length === 0 ? `<tr><td colspan="4" class="py-8 text-center text-slate-400">Aún no se han registrado goles en partidos finalizados.</td></tr>` : ""}
    ${g.map((x, i) => `<tr class="border-b border-slate-50 last:border-0"><td class="py-2.5 px-3 text-center text-slate-500 font-semibold">${i + 1}</td>
      <td class="py-2.5 px-3 font-medium text-slate-700">${esc(x.nombre_completo)}</td><td class="py-2.5 px-3 text-slate-500">${esc(nombreEquipo(x.equipo_id))}</td>
      <td class="py-2.5 px-3 text-center font-extrabold text-emerald-700">${x.goles}</td></tr>`).join("")}
  </tbody></table></div>`;
}

/* ============================================================
   8. PANTALLA 2 — PLANILLA DIGITAL DEL ÁRBITRO (rol Arbitro)
   ============================================================ */
async function cargarArbitro() {
  const a = state.arb;
  a.partidos = (await GET("/partidos/mis-asignaciones")).sort((x, y) => x.fecha_hora.localeCompare(y.fecha_hora));
  if (!porId(a.partidos, a.id)) {
    const activo = a.partidos.find((p) => p.estado === "En_Juego") || a.partidos.find((p) => p.estado === "Programado") || a.partidos[0];
    a.id = activo ? activo.id : null;
  }
  await cargarDetallePartido();
}
async function cargarDetallePartido() {
  const a = state.arb;
  clearInterval(a.timerId); a.running = false; a.modal = null;
  const p = porId(a.partidos, a.id);
  if (!p) { a.marcador = null; a.alin = []; a.eventos = []; a.seconds = 0; return; }
  const fase = await GET(`/fases/${p.fase_id}`);
  await cargarNombres(fase.torneo_id);
  [a.marcador, a.alin, a.eventos] = await Promise.all([GET(`/partidos/${p.id}/marcador`), GET(`/partidos/${p.id}/alineaciones`), GET(`/partidos/${p.id}/eventos`)]);
  a.seconds = a.eventos.length ? Math.max(...a.eventos.map((e) => e.minuto_ocurrencia)) * 60 : 0;
}
async function recargarPartidoArbitro() {
  const a = state.arb;
  a.partidos = (await GET("/partidos/mis-asignaciones")).sort((x, y) => x.fecha_hora.localeCompare(y.fecha_hora));
  const p = porId(a.partidos, a.id);
  [a.marcador, a.eventos] = await Promise.all([GET(`/partidos/${p.id}/marcador`), GET(`/partidos/${p.id}/eventos`)]);
}
const jugadorDeAlineacion = (id) => state.arb.alin.find((x) => x.jugador_id === id);
const cerrado = (p) => p.estado === "Finalizado" || p.estado === "W_O";
function formatoReloj(s) { return `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`; }

function renderArbitro() {
  const a = state.arb, p = porId(a.partidos, a.id);
  if (!p) return vacio("No tienes partidos asignados. El Administrador debe designarte como árbitro de un partido.");
  const enJuego = p.estado === "En_Juego", fin = cerrado(p), programado = p.estado === "Programado";
  const m = a.marcador || { goles_local: 0, goles_visitante: 0 };
  const eventos = [...a.eventos].reverse();
  return `
  <div class="min-h-screen bg-slate-50 pb-8"><div class="max-w-md mx-auto">
    <div class="px-4 pt-4">${filterDropdown(a.id, a.partidos.map((x) => ({ value: x.id, label: `${nombreEquipo(x.equipo_local_id)} vs ${nombreEquipo(x.equipo_visitante_id)} · ${fechaDe(x.fecha_hora)} ${horaDe(x.fecha_hora)}` })), null, "select-partido")}</div>
    <div class="mx-4 mt-3 rounded-xl bg-blue-950 text-white p-4">
      <div class="flex items-center justify-between mb-3">
        <span class="inline-flex items-center gap-2 text-[11px] font-bold px-3 py-1 rounded-full ${enJuego ? "bg-red-600" : "bg-slate-600"}">${enJuego ? "EN VIVO" : esc(p.estado.replace("_", " ").toUpperCase())}</span>
        <span class="text-[11px] text-blue-200/70">${esc(fechaDe(p.fecha_hora))} ${esc(horaDe(p.fecha_hora))}</span>
      </div>
      <div class="flex items-center justify-between gap-3">
        <div class="flex-1 text-center text-xs font-semibold leading-tight">${esc(nombreEquipo(p.equipo_local_id))}</div>
        <div class="text-3xl font-extrabold tabular-nums px-2">${m.goles_local}&nbsp;–&nbsp;${m.goles_visitante}</div>
        <div class="flex-1 text-center text-xs font-semibold leading-tight">${esc(nombreEquipo(p.equipo_visitante_id))}</div>
      </div>
      <div class="flex items-center justify-center gap-3 mt-4">
        <div id="reloj" class="font-mono text-xl font-bold tabular-nums bg-white/10 px-4 py-1.5 rounded-lg">${formatoReloj(a.seconds)}</div>
        ${programado ? `<button data-action="iniciar-partido" class="${BTN} flex items-center gap-1.5">Iniciar partido</button>` : ""}
        ${enJuego ? `<button data-action="toggle-timer" class="${BTN} flex items-center gap-1.5"><i data-lucide="${a.running ? "pause" : "play"}" class="w-3.5 h-3.5"></i>${a.running ? "Pausar reloj" : "Iniciar reloj"}</button>` : ""}
      </div>
      ${programado && !a.alin.length ? `<p class="text-[11px] text-amber-300 text-center mt-3">Aún no hay alineaciones enviadas; sin las dos planillas no se puede iniciar.</p>` : ""}
    </div>
    <div class="grid grid-cols-2 gap-3 px-4 mt-4">${equipoAcciones(p.equipo_local_id, !enJuego, "local")}${equipoAcciones(p.equipo_visitante_id, !enJuego, "visitante")}</div>
    <div class="px-4 mt-6"><h3 class="text-xs font-semibold text-blue-950 mb-2 uppercase tracking-wide">Línea de tiempo</h3><div class="flex flex-col gap-2">
      ${eventos.length === 0 ? `<p class="text-xs text-slate-400 text-center py-6">Sin eventos registrados todavía.</p>` : ""}
      ${eventos.map((ev) => { const meta = EVENT_META[ev.tipo_evento] || { label: ev.tipo_evento, icon: "•", bg: "bg-slate-50" }; const j = jugadorDeAlineacion(ev.jugador_id), s = ev.jugador_secundario_id ? jugadorDeAlineacion(ev.jugador_secundario_id) : null; return `
      <div class="flex items-center gap-3 rounded-lg border border-slate-100 px-3 py-2.5 ${meta.bg}">
        <span class="font-mono text-xs font-bold text-slate-500 w-8 shrink-0">${ev.minuto_ocurrencia}'</span><span class="text-base shrink-0">${meta.icon}</span>
        <div class="flex-1 min-w-0"><p class="text-xs font-semibold text-slate-700 truncate">#${j ? j.numero_camiseta ?? "-" : "?"} ${esc(j ? j.nombre_completo : "Jugador " + ev.jugador_id)}${s ? ` <span class="font-normal text-slate-500">${ev.tipo_evento === "Sustitucion" ? "por" : "asist."} ${esc(s.nombre_completo)}</span>` : ""}</p>
        <p class="text-[11px] text-slate-500 truncate">${meta.label} · ${esc(nombreEquipo(ev.equipo_id))}</p></div>
        ${enJuego ? `<button data-action="eliminar-evento" data-evento-id="${ev.id}" class="p-1.5 rounded-md text-slate-400 hover:text-red-600 hover:bg-white shrink-0" title="Eliminar evento"><i data-lucide="trash-2" class="w-3.5 h-3.5"></i></button>` : ""}
      </div>`; }).join("")}
    </div></div>
    <div class="px-4 mt-6">
      ${fin ? `<div class="text-center text-xs font-semibold text-slate-500 bg-slate-100 rounded-xl py-3">Planilla confirmada — marcador final ${m.goles_local} – ${m.goles_visitante}</div>`
            : enJuego ? `<button data-action="finalizar-partido" class="w-full bg-blue-950 hover:bg-blue-900 text-white text-sm font-bold py-4 rounded-xl">Finalizar partido y confirmar planilla</button>` : ""}
    </div>
  </div>${a.modal ? selectorJugadorModal(a.modal, p) : ""}</div>`;
}
function equipoAcciones(idEquipo, deshabilitado, lado) {
  const b = (tipo, clases, texto) => `<button ${deshabilitado ? "disabled" : ""} data-action="abrir-modal" data-tipo="${tipo}" data-equipo="${lado}" class="flex items-center justify-center gap-1.5 ${clases} disabled:opacity-40 text-xs font-bold py-3 rounded-lg">${texto}</button>`;
  return `<div class="bg-white rounded-xl shadow-sm p-3"><p class="text-[11px] font-bold text-slate-500 text-center mb-2 truncate">${esc(nombreEquipo(idEquipo))}</p><div class="flex flex-col gap-2">
    ${b("Gol", "bg-emerald-600 hover:bg-emerald-700 text-white", "⚽ + GOL")}${b("Tarjeta_Amarilla", "bg-amber-400 hover:bg-amber-500 text-blue-950", "🟨 AMARILLA")}
    ${b("Tarjeta_Roja", "bg-red-600 hover:bg-red-700 text-white", "🟥 ROJA")}${b("Sustitucion", "bg-blue-100 hover:bg-blue-200 text-blue-950", "🔁 CAMBIO")}</div></div>`;
}
function selectorJugadorModal(modal, p) {
  const idEquipo = modal.equipo === "local" ? p.equipo_local_id : p.equipo_visitante_id;
  const meta = EVENT_META[modal.tipo];
  let jugadores = state.arb.alin.filter((x) => x.equipo_id === idEquipo);
  let instruccion = "Selecciona al jugador";
  if (modal.tipo === "Sustitucion") {
    if (!modal.sale) { jugadores = jugadores.filter((x) => x.es_titular); instruccion = "¿Quién SALE?"; }
    else { jugadores = jugadores.filter((x) => !x.es_titular); instruccion = "¿Quién ENTRA? (suplente)"; }
  }
  return `
  <div class="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/50 px-0 sm:px-4">
    <div class="bg-white w-full sm:max-w-md rounded-t-2xl sm:rounded-2xl p-4 max-h-[82vh] overflow-y-auto">
      <div class="flex items-center justify-between mb-1">
        <div class="flex items-center gap-2"><span class="text-lg">${meta.icon}</span><div><p class="text-sm font-bold text-blue-950">${meta.label}</p><p class="text-[11px] text-slate-500">${esc(nombreEquipo(idEquipo))}</p></div></div>
        <button data-action="cerrar-modal" class="p-1.5 rounded-md text-slate-400 hover:bg-slate-100"><i data-lucide="x" class="w-4 h-4"></i></button>
      </div>
      <p class="text-[11px] text-slate-400 mt-3 mb-2 uppercase tracking-wide font-semibold">${instruccion}</p>
      ${jugadores.length === 0 ? `<p class="text-xs text-slate-400 py-4 text-center">Este equipo no tiene jugadores en la alineación.</p>` : ""}
      <div class="grid grid-cols-3 gap-2">${jugadores.map((j) => `
        <button data-action="registrar-evento" data-jugador-id="${j.jugador_id}" data-equipo-id="${idEquipo}" class="flex flex-col items-center justify-center rounded-lg py-2.5 text-center border border-blue-950 bg-blue-950 text-white hover:bg-blue-900">
          <span class="text-sm font-extrabold">${j.numero_camiseta ?? "-"}</span><span class="text-[9px] leading-tight mt-0.5 px-1 truncate w-full">${esc(j.nombre_completo)}</span>
          <span class="text-[8px] text-blue-200">${j.es_titular ? "titular" : "suplente"}</span></button>`).join("")}</div>
    </div>
  </div>`;
}

/* ============================================================
   9. PANTALLA 3 — PANEL DEL ENTRENADOR (rol Entrenador)
   ============================================================ */
async function cargarCoach() {
  const c = state.coach;
  [c.equipos, c.colegios, c.torneos] = await Promise.all([GET("/equipos/mis-equipos"), GET("/colegios/"), GET("/torneos/")]);
  if (!porId(c.equipos, c.equipoId)) c.equipoId = c.equipos.length ? c.equipos[0].id : null;
  c.showEquipo = c.showEquipo && true;
  await cargarDetalleEquipo();
}
async function cargarDetalleEquipo() {
  const c = state.coach, eq = porId(c.equipos, c.equipoId);
  if (!eq) { c.jugadores = []; c.calendario = []; return; }
  await cargarNombres(eq.torneo_id).catch(() => {});
  state.nombres[eq.id] = state.nombres[eq.id] || eq.nombre;
  [c.jugadores, c.calendario] = await Promise.all([GET(`/equipos/${eq.id}/jugadores?solo_activos=true`), GET(`/equipos/${eq.id}/calendario`)]);
}
const reglaDe = (torneo, clave, defecto) => { const v = torneo && torneo.reglas ? torneo.reglas[clave] : undefined; return Number.isInteger(v) ? v : defecto; };
const BADGE_INSCRIPCION = { Preinscrito: "bg-slate-100 text-slate-600", Pago_Pendiente: "bg-amber-50 text-amber-700", Habilitado: "bg-emerald-50 text-emerald-700", Descalificado: "bg-red-50 text-red-700" };

function renderCoach() {
  const c = state.coach, eq = porId(c.equipos, c.equipoId);
  const torneo = eq ? porId(c.torneos, eq.torneo_id) : null;
  const colegio = eq ? porId(c.colegios, eq.colegio_id) : null;
  const maximo = reglaDe(torneo, "max_jugadores", 25);
  const puedePagar = eq && (eq.estado_inscripcion === "Preinscrito" || eq.estado_inscripcion === "Pago_Pendiente");
  return `
  <div class="min-h-screen bg-slate-50 pb-16"><div class="mx-auto max-w-4xl px-4 pt-6">
    <div class="flex flex-wrap items-center gap-3">
      ${c.equipos.length ? filterDropdown(c.equipoId, c.equipos.map((x) => ({ value: x.id, label: x.nombre })), null, "select-equipo") : ""}
      <button data-action="toggle-form-equipo" class="text-xs font-semibold text-blue-900 underline underline-offset-2">${c.equipos.length && !c.showEquipo ? "+ Inscribir otro equipo" : c.showEquipo ? "Ocultar formulario" : ""}</button>
    </div>
    ${!c.equipos.length || c.showEquipo ? formularioEquipoHTML() : ""}
    ${!eq ? "" : `
    <div class="bg-white rounded-xl shadow-sm p-5 mt-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div class="flex items-center gap-3">
        <div class="w-12 h-12 rounded-lg bg-blue-950 text-white flex items-center justify-center font-bold text-sm shrink-0">${esc(siglaDe(eq.nombre))}</div>
        <div><p class="text-sm font-bold text-blue-950">${esc(eq.nombre)}</p>
          <p class="text-xs text-slate-500 mt-0.5">${esc(colegio ? colegio.nombre : "Colegio #" + eq.colegio_id)} · ${esc(torneo ? torneo.nombre + " (" + torneo.categoria + ")" : "")}</p>
          <p class="text-xs text-slate-500">${c.jugadores.length} / ${maximo} jugadores${eq.plantilla_bloqueada ? " · plantilla bloqueada" : ""}</p></div>
      </div>
      <div class="flex items-center gap-3 flex-wrap">
        <span class="px-3 py-1.5 rounded-full text-xs font-bold ${BADGE_INSCRIPCION[eq.estado_inscripcion] || ""}">${esc(eq.estado_inscripcion.replace("_", " "))}</span>
        ${puedePagar ? `<button data-action="abrir-pago-modal" class="${BTN} flex items-center gap-1.5"><i data-lucide="credit-card" class="w-3.5 h-3.5"></i> Reportar pago de inscripción</button>` : ""}
      </div>
    </div>
    ${eq.plantilla_bloqueada || eq.estado_inscripcion === "Descalificado" ? "" : formularioJugadorHTML()}
    <div class="bg-white rounded-xl shadow-sm overflow-hidden mt-6">
      <div class="px-5 py-4 border-b border-slate-100"><h3 class="text-sm font-bold text-blue-950">Plantilla / nómina de jugadores</h3></div>
      <div class="overflow-x-auto"><table class="w-full text-xs"><thead><tr class="text-slate-400 border-b border-slate-100">${TH("#", 4)}<th class="py-2.5 px-3 text-left font-medium">JUGADOR</th>${TH("POSICIÓN", 3)}${TH("ESTADO", 3)}${TH("ACCIONES", 4)}</tr></thead><tbody>
        ${c.jugadores.length === 0 ? `<tr><td colspan="5" class="py-8 text-center text-slate-400">Aún no hay jugadores inscritos en este equipo.</td></tr>` : ""}
        ${c.jugadores.map((j) => `<tr class="border-b border-slate-50 last:border-0">
          <td class="py-2.5 px-4 text-center">${j.numero_camiseta != null ? `<span class="inline-flex items-center justify-center w-7 h-7 rounded-full bg-blue-950 text-white font-bold text-[11px]">${j.numero_camiseta}</span>` : "-"}</td>
          <td class="py-2.5 px-3"><p class="font-medium text-slate-700">${esc(j.nombre_completo)}</p><p class="text-[11px] text-slate-400">${esc(j.identificacion)}</p></td>
          <td class="py-2.5 px-3 text-center">${j.posicion ? `<span class="px-2.5 py-1 rounded-full text-[10.5px] font-semibold ${POSICION_COLOR[j.posicion] || "bg-slate-100 text-slate-600"}">${esc(j.posicion)}</span>` : "-"}</td>
          <td class="py-2.5 px-3 text-center">${j.sancionado ? `<span class="text-red-600 font-semibold text-[11px]">Sancionado${j.fechas_suspension ? " (" + j.fechas_suspension + " fecha/s)" : ""}</span>` : `<span class="text-emerald-600 font-semibold text-[11px]">Habilitado</span>`}</td>
          <td class="py-2.5 px-4 text-center">${eq.plantilla_bloqueada ? "" : `<button data-action="eliminar-jugador" data-jugador-id="${j.id}" class="p-1.5 rounded-md text-slate-400 hover:text-red-600 hover:bg-slate-50" title="Dar de baja"><i data-lucide="trash-2" class="w-3.5 h-3.5"></i></button>`}</td></tr>`).join("")}
      </tbody></table></div>
    </div>
    <div class="bg-white rounded-xl shadow-sm overflow-hidden mt-6">
      <div class="px-5 py-4 border-b border-slate-100"><h3 class="text-sm font-bold text-blue-950">Calendario y planillas</h3></div>
      ${c.calendario.length === 0 ? `<p class="py-8 text-center text-xs text-slate-400">Todavía no hay partidos programados para este equipo.</p>` : ""}
      ${c.calendario.map((p) => `<div class="flex items-center gap-3 px-5 py-3 border-b border-slate-50 last:border-0 text-xs">
        <span class="text-slate-400 w-28 shrink-0">${esc(fechaDe(p.fecha_hora))} ${esc(horaDe(p.fecha_hora))}</span>
        <span class="flex-1 font-medium text-slate-700">${esc(nombreEquipo(p.equipo_local_id))} vs ${esc(nombreEquipo(p.equipo_visitante_id))}</span>
        <span class="text-slate-500">${esc(p.estado.replace("_", " "))}</span>
        ${p.estado === "Programado" ? `<button data-action="abrir-planilla" data-partido-id="${p.id}" class="${BTN}">Enviar planilla</button>` : ""}</div>`).join("")}
    </div>`}
  </div>
  ${c.showPago && eq ? pagoModalHTML(eq) : ""}${c.planilla ? planillaModalHTML(torneo) : ""}</div>`;
}
function formularioEquipoHTML() {
  const c = state.coach;
  const abiertos = c.torneos.filter((t) => t.estado === "Inscripciones");
  return `<form id="form-equipo" class="bg-white rounded-xl shadow-sm p-5 mt-4"><h3 class="text-sm font-bold text-blue-950 mb-4">Inscribir equipo</h3>
    ${abiertos.length === 0 ? `<p class="text-xs text-slate-500">No hay torneos con inscripciones abiertas.</p>` : `
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
      ${campo("Torneo", `<select name="torneo_id" class="${INPUT}">${abiertos.map((t) => `<option value="${t.id}">${esc(t.nombre)} · ${esc(t.categoria)}</option>`).join("")}</select>`)}
      ${campo("Colegio", `<select name="colegio_id" class="${INPUT}">${c.colegios.map((x) => `<option value="${x.id}">${esc(x.nombre)}</option>`).join("")}</select>`)}
      ${campo("Nombre del equipo", entrada("nombre", "Ej. Selección Prejuvenil", "required"))}
    </div><button type="submit" class="${BTN} mt-4">+ Inscribir equipo</button>`}</form>`;
}
function formularioJugadorHTML() {
  return `<form id="form-jugador" class="bg-white rounded-xl shadow-sm p-5 mt-6"><h3 class="text-sm font-bold text-blue-950 mb-4">Inscribir jugador</h3>
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
      ${campo("Nombre completo", entrada("nombre_completo", "Ej. Camilo Reyes", "required"))}
      ${campo("Documento de identidad (TI/CC)", entrada("identificacion", "Ej. 1098234099", "required"))}
      ${campo("Fecha de nacimiento", entrada("fecha_nacimiento", "", 'type="date" required'))}
      ${campo("Número de camiseta (0-99)", entrada("numero_camiseta", "Ej. 10", 'type="number" min="0" max="99"'))}
      ${campo("Posición", `<select name="posicion" class="${INPUT}"><option value="">Sin definir</option>${POSICIONES.map((p) => `<option>${p}</option>`).join("")}</select>`)}
    </div><button type="submit" class="${BTN} mt-4">+ Inscribir jugador</button></form>`;
}
function pagoModalHTML(eq) {
  return `<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4"><form id="form-pago" class="bg-white rounded-2xl p-5 max-w-sm w-full">
    <p class="text-sm font-bold text-blue-950 mb-1">Reportar pago de inscripción</p><p class="text-xs text-slate-500 mb-4">Equipo <b>${esc(eq.nombre)}</b>. El Administrador validará el comprobante.</p>
    <div class="flex flex-col gap-3">
      ${campo("Monto (COP)", entrada("monto", "150000", 'type="number" min="1" step="0.01" required'))}
      ${campo("Método de pago", `<select name="metodo_pago" class="${INPUT}"><option>Transferencia</option><option>Consignación</option><option>Efectivo</option></select>`)}
      ${campo("Referencia de la transacción", entrada("referencia_transaccion", "Nº de comprobante"))}
      ${campo("Enlace al comprobante (opcional)", entrada("comprobante_url", "https://…"))}
    </div>
    <div class="flex justify-end gap-2 mt-4"><button type="button" data-action="cerrar-pago-modal" class="text-xs font-semibold text-slate-500 px-3 py-2 rounded-lg hover:bg-slate-50">Cancelar</button><button type="submit" class="${BTN}">Enviar pago</button></div>
  </form></div>`;
}
function planillaModalHTML(torneo) {
  const c = state.coach, pl = c.planilla, tit = reglaDe(torneo, "titulares", 11), sup = reglaDe(torneo, "max_suplentes", 7);
  const p = porId(c.calendario, pl.partidoId);
  const cuenta = (v) => Object.values(pl.roles).filter((x) => x === v).length;
  return `<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4"><form id="form-planilla" class="bg-white rounded-2xl p-5 max-w-lg w-full max-h-[85vh] overflow-y-auto">
    <p class="text-sm font-bold text-blue-950">Planilla: ${esc(nombreEquipo(p.equipo_local_id))} vs ${esc(nombreEquipo(p.equipo_visitante_id))}</p>
    <p class="text-xs text-slate-500 mb-3">Exactamente ${tit} titulares y máximo ${sup} suplentes. Seleccionados: <b id="conteo-planilla">${cuenta("titular")} titulares, ${cuenta("suplente")} suplentes</b>.</p>
    <div class="flex flex-col gap-1.5">${c.jugadores.map((j) => `<div class="flex items-center gap-2 text-xs ${j.sancionado ? "opacity-50" : ""}">
      <span class="w-8 text-center font-bold text-blue-950">${j.numero_camiseta ?? "-"}</span><span class="flex-1 truncate">${esc(j.nombre_completo)}${j.sancionado ? " (sancionado)" : ""}</span>
      <select data-role="rol-jugador" data-jugador-id="${j.id}" ${j.sancionado ? "disabled" : ""} class="border border-slate-200 rounded-md px-2 py-1 text-[11px]">
        ${["no", "titular", "suplente"].map((r) => `<option value="${r}" ${pl.roles[j.id] === r ? "selected" : ""}>${r === "no" ? "No convocado" : r === "titular" ? "Titular" : "Suplente"}</option>`).join("")}</select></div>`).join("")}</div>
    <div class="flex justify-end gap-2 mt-4"><button type="button" data-action="cerrar-planilla" class="text-xs font-semibold text-slate-500 px-3 py-2 rounded-lg hover:bg-slate-50">Cancelar</button><button type="submit" class="${BTN}">Enviar planilla</button></div>
  </form></div>`;
}

/* ============================================================
   10. PANTALLA 4 — PANEL DEL ADMINISTRADOR (rol Administrador)
   ============================================================ */
async function cargarAdmin() {
  const s = state.admin;
  [s.torneos, s.canchas, s.colegios, s.usuarios, s.pagos] = await Promise.all([
    GET("/torneos/"), GET("/canchas/?solo_activas=false"), GET("/colegios/?activos_solamente=false"), GET("/usuarios/"), GET("/pagos/?estado=Pendiente"),
  ]);
  if (!porId(s.torneos, s.torneoId)) s.torneoId = s.torneos.length ? s.torneos[0].id : null;
  await cargarTorneoAdmin();
}
async function cargarTorneoAdmin() {
  const s = state.admin;
  s.fases = []; s.equipos = []; s.partidos = []; s.tablas = [];
  if (s.torneoId == null) { s.faseId = null; return; }
  [s.fases, s.equipos] = await Promise.all([GET(`/torneos/${s.torneoId}/fases`), GET(`/torneos/${s.torneoId}/equipos`)]);
  s.equipos.forEach((e) => { state.nombres[e.id] = e.nombre; });
  if (!porId(s.fases, s.faseId)) s.faseId = s.fases.length ? s.fases[0].id : null;
  await cargarFaseAdmin();
}
async function cargarFaseAdmin() {
  const s = state.admin;
  s.partidos = []; s.tablas = [];
  if (s.faseId == null) return;
  [s.partidos, s.tablas] = await Promise.all([GET(`/fases/${s.faseId}/partidos`), GET(`/fases/${s.faseId}/tablas`)]);
}
async function recargarAdmin() { await cargarAdmin(); render(); }

function renderAdmin() {
  const s = state.admin;
  return `
  <div class="min-h-screen bg-slate-50"><div class="flex flex-col md:flex-row">
    <aside class="w-full md:w-60 shrink-0 bg-blue-950 md:min-h-[calc(100vh-60px)] px-3 py-4"><div class="flex md:flex-col gap-1 overflow-x-auto">
      ${ADMIN_SECTIONS.map((sec) => `<button data-action="admin-section" data-section="${sec.id}" class="text-left whitespace-nowrap px-3 py-2.5 rounded-lg text-xs font-semibold transition-colors ${s.section === sec.id ? "bg-white text-blue-950" : "text-blue-200/75 hover:bg-white/10 hover:text-white"}">${sec.label}</button>`).join("")}
    </div></aside>
    <main class="flex-1 px-4 sm:px-6 py-6 min-w-0">
      <div class="flex items-center justify-between flex-wrap gap-2 mb-6"><h2 class="text-lg font-bold text-blue-950">${ADMIN_SECTIONS.find((x) => x.id === s.section).label}</h2>
        ${["TORNEOS", "FIXTURES", "INSTITUCIONES"].includes(s.section) && s.torneos.length ? filterDropdown(s.torneoId, s.torneos.map((t) => ({ value: t.id, label: `${t.nombre} · ${t.categoria} (${t.estado.replace("_", " ")})` })), null, "admin-torneo") : ""}</div>
      ${s.section === "TORNEOS" ? seccionTorneosHTML() : ""}${s.section === "FIXTURES" ? seccionFixturesHTML() : ""}
      ${s.section === "SEDES" ? seccionSedesHTML() : ""}${s.section === "INSTITUCIONES" ? seccionInstitucionesHTML() : ""}${s.section === "USUARIOS" ? seccionUsuariosHTML() : ""}
    </main></div></div>`;
}
const card = (titulo, cuerpo) => `<div class="bg-white rounded-xl shadow-sm p-5"><h3 class="text-sm font-bold text-blue-950 mb-4">${titulo}</h3>${cuerpo}</div>`;

function seccionTorneosHTML() {
  const s = state.admin, t = porId(s.torneos, s.torneoId);
  const acciones = !t ? "" : [
    t.estado === "Inscripciones" ? `<button data-action="torneo-iniciar" class="${BTN}">Iniciar torneo</button>` : "",
    t.estado === "En_Curso" ? `<button data-action="torneo-finalizar" class="${BTN}">Finalizar torneo</button>` : "",
    t.estado === "Inscripciones" || t.estado === "En_Curso" ? `<button data-action="torneo-cancelar" class="text-xs font-bold text-red-600 border border-red-200 px-4 py-2 rounded-lg hover:bg-red-50">Cancelar torneo</button>` : "",
  ].join(" ");
  return `<div class="flex flex-col gap-6">
    ${card("Crear torneo", `<form id="form-torneo"><div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
      ${campo("Nombre", entrada("nombre", "Copa Intercolegiada 2026", "required"))}${campo("Categoría", entrada("categoria", "Sub-17", "required"))}<div></div>
      ${campo("Fecha de inicio", entrada("fecha_inicio", "", 'type="date" required'))}${campo("Fecha de fin", entrada("fecha_fin", "", 'type="date" required'))}<div></div>
      ${campo("Mín. jugadores por equipo", entrada("min_jugadores", "", 'type="number" min="1" value="11"'))}${campo("Máx. jugadores por equipo", entrada("max_jugadores", "", 'type="number" min="1" value="25"'))}${campo("Mín. equipos para iniciar", entrada("min_equipos", "", 'type="number" min="2" value="2"'))}
      ${campo("Titulares por planilla", entrada("titulares", "", 'type="number" min="1" value="11"'))}${campo("Máx. suplentes por planilla", entrada("max_suplentes", "", 'type="number" min="0" value="7"'))}
      </div><button type="submit" class="${BTN} mt-4">+ Crear torneo</button></form>`)}
    ${!t ? "" : card(`${esc(t.nombre)} · ${esc(t.categoria)}`, `
      <p class="text-xs text-slate-500 mb-3">Estado: <b>${esc(t.estado.replace("_", " "))}</b> · ${esc(t.fecha_inicio)} → ${esc(t.fecha_fin)} · ${s.equipos.filter((e) => e.estado_inscripcion === "Habilitado").length} equipos habilitados</p>
      <div class="flex gap-2 flex-wrap mb-5">${acciones}</div>
      <h4 class="text-xs font-bold text-blue-950 uppercase tracking-wide mb-2">Fases</h4>
      <ol class="text-xs text-slate-700 mb-3 list-decimal pl-5">${s.fases.length ? s.fases.map((f) => `<li>${esc(f.nombre)} — ${esc(f.tipo_formato.replace("_", " "))} · ${esc(f.estado.replace("_", " "))}</li>`).join("") : "<li class='list-none -ml-5 text-slate-400'>Sin fases todavía.</li>"}</ol>
      ${t.estado === "Inscripciones" ? `<form id="form-fase" class="flex gap-2 flex-wrap items-end">${campo("Nombre de la fase", entrada("nombre", "Fase de Grupos", "required"))}${campo("Formato", `<select name="tipo_formato" class="${INPUT}"><option value="Grupos">Grupos</option><option value="Eliminatoria_Directa">Eliminatoria directa</option></select>`)}<button type="submit" class="${BTN}">+ Agregar fase</button></form>` : ""}`)}
  </div>`;
}

function seccionFixturesHTML() {
  const s = state.admin, t = porId(s.torneos, s.torneoId), fase = porId(s.fases, s.faseId);
  if (!t) return `<p class="text-xs text-slate-400">Crea un torneo primero.</p>`;
  if (!s.fases.length) return `<p class="text-xs text-slate-400">El torneo no tiene fases.</p>`;
  const arbitros = s.usuarios.filter((u) => u.rol === "Arbitro" && u.estado_activo);
  const habilitados = s.equipos.filter((e) => e.estado_inscripcion === "Habilitado");
  const sinGrupos = fase && fase.tipo_formato === "Grupos" && !s.tablas.length;
  const orden = [...s.partidos].sort((a, b) => a.fecha_hora.localeCompare(b.fecha_hora));
  return `<div class="flex flex-col gap-6">
    ${card("Fase y fixture", `
      <div class="flex flex-wrap gap-3 items-end mb-4">${filterDropdown(s.faseId, s.fases.map((f) => ({ value: f.id, label: `${f.nombre} (${f.estado.replace("_", " ")})` })), null, "admin-fase")}</div>
      ${t.estado !== "En_Curso" ? `<p class="text-xs text-amber-700">El torneo debe estar En curso para armar grupos y generar el fixture.</p>` : ""}
      ${t.estado === "En_Curso" && fase && fase.estado === "Programada" && sinGrupos ? `
        <form id="form-grupos" class="flex gap-2 items-end flex-wrap mb-3">${campo(`Número de grupos (${habilitados.length} equipos habilitados)`, entrada("n", "", 'type="number" min="1" max="16" value="2" required'))}<button type="submit" class="${BTN}">Armar grupos automáticamente</button></form>` : ""}
      ${t.estado === "En_Curso" && fase && fase.estado === "Programada" && !sinGrupos && !s.partidos.length ? `
        <label class="flex items-center gap-2 text-xs text-slate-600 mb-3"><input type="checkbox" id="chk-arbitros" checked> Asignar árbitros libres automáticamente</label>
        <button data-action="generar-fixture" class="${BTN} flex items-center gap-2">⚡ Generar fixture automático</button>
        <p class="text-[11px] text-slate-400 mt-2">Crea los cruces con cancha, fecha y hora sin choques. Si no alcanzan los horarios del torneo, no se crea nada.</p>` : ""}
      ${s.tablas.length ? `<div class="mt-4 flex gap-2 flex-wrap">${s.tablas.map((tb) => `<span class="text-[11px] bg-slate-100 rounded-full px-3 py-1">${esc(tb.nombre_grupo)}: ${tb.estado_cierre ? "cerrado" : `<button data-action="cerrar-grupo" data-tabla-id="${tb.id}" class="font-bold text-emerald-700 underline">cerrar grupo</button>`}</span>`).join("")}</div>` : ""}
      ${fase && fase.estado !== "Finalizada" && t.estado === "En_Curso" && s.partidos.length ? `<button data-action="cerrar-fase" class="mt-4 text-xs font-bold text-blue-950 border border-blue-200 px-4 py-2 rounded-lg hover:bg-blue-50">Cerrar fase</button>` : ""}
    `)}
    <div class="bg-white rounded-xl shadow-sm overflow-hidden"><div class="px-5 py-4 border-b border-slate-100"><h3 class="text-sm font-bold text-blue-950">Partidos de la fase</h3></div>
      <div class="overflow-x-auto"><table class="w-full text-xs"><thead><tr class="text-slate-400 border-b border-slate-100"><th class="py-2.5 px-4 text-left font-medium">FECHA / HORA</th><th class="py-2.5 px-3 text-left font-medium">PARTIDO</th><th class="py-2.5 px-3 text-left font-medium">CANCHA / ÁRBITRO</th><th class="py-2.5 px-3 text-left font-medium">ESTADO</th></tr></thead><tbody>
      ${orden.length === 0 ? `<tr><td colspan="4" class="py-8 text-center text-slate-400">Esta fase aún no tiene partidos.</td></tr>` : ""}
      ${orden.map((p) => { const editable = p.estado === "Programado" || p.estado === "Suspendido"; return `<tr class="border-b border-slate-50 last:border-0 align-top">
        <td class="py-2.5 px-4"><div class="flex flex-col gap-1">
          <input type="date" ${editable ? "" : "disabled"} data-action="reprogramar" data-id="${p.id}" data-campo="fecha" value="${fechaDe(p.fecha_hora)}" class="border border-slate-200 rounded-md px-2 py-1 text-[11px]">
          <input type="time" ${editable ? "" : "disabled"} data-action="reprogramar" data-id="${p.id}" data-campo="hora" value="${horaDe(p.fecha_hora)}" class="border border-slate-200 rounded-md px-2 py-1 text-[11px]"></div></td>
        <td class="py-2.5 px-3 font-medium text-slate-700">${esc(nombreEquipo(p.equipo_local_id))} <span class="text-slate-400 font-normal">vs</span> ${esc(nombreEquipo(p.equipo_visitante_id))}</td>
        <td class="py-2.5 px-3"><div class="flex flex-col gap-1">
          <select ${editable ? "" : "disabled"} data-action="reprogramar" data-id="${p.id}" data-campo="cancha" class="border border-slate-200 rounded-md px-2 py-1.5 text-[11px]">${s.canchas.map((c) => `<option value="${c.id}" ${c.id === p.cancha_id ? "selected" : ""}>${esc(c.nombre)}${c.estado_activo ? "" : " (inactiva)"}</option>`).join("")}</select>
          <select ${p.estado === "Programado" ? "" : "disabled"} data-action="asignar-arbitro" data-id="${p.id}" class="border border-slate-200 rounded-md px-2 py-1.5 text-[11px]"><option value="">${p.arbitro_id ? "" : "— sin árbitro —"}</option>${arbitros.map((a) => `<option value="${a.id}" ${a.id === p.arbitro_id ? "selected" : ""}>${esc(a.nombre_completo)}</option>`).join("")}</select></div></td>
        <td class="py-2.5 px-3"><span class="font-semibold">${esc(p.estado.replace("_", " "))}</span>${p.estado === "Programado" ? `<div class="mt-1"><button data-action="suspender-partido" data-id="${p.id}" class="text-[11px] text-amber-700 underline">Suspender</button> · <button data-action="walkover" data-id="${p.id}" class="text-[11px] text-red-600 underline">W.O.</button></div>` : ""}</td></tr>`; }).join("")}
      </tbody></table></div></div></div>`;
}

function seccionSedesHTML() {
  const s = state.admin;
  return `<div class="flex flex-col gap-6">
    ${card("Registrar nueva sede / cancha", `<form id="form-cancha"><div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
      ${campo("Nombre", entrada("nombre", "Cancha 4 — Villa Olímpica", "required"))}${campo("Dirección", entrada("direccion_sede", "Cra 20 #5-40", "required"))}
      ${campo("Superficie", `<select name="tipo_superficie" class="${INPUT}">${SUPERFICIES.map((x) => `<option>${x}</option>`).join("")}</select>`)}</div>
      <button type="submit" class="${BTN} mt-4">+ Registrar sede</button></form>`)}
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">${s.canchas.map((c) => `<div class="bg-white rounded-xl shadow-sm p-4 ${c.estado_activo ? "" : "opacity-60"}">
      <p class="text-sm font-bold text-blue-950">${esc(c.nombre)}</p><p class="text-[11px] text-slate-500 mt-0.5">${esc(c.direccion_sede)}</p><p class="text-[11px] text-slate-500">Superficie: ${esc(c.tipo_superficie || "—")}</p>
      <button data-action="toggle-cancha" data-id="${c.id}" class="mt-3 text-[11px] font-semibold text-blue-900 underline underline-offset-2">${c.estado_activo ? "Inhabilitar" : "Habilitar"}</button></div>`).join("")}</div></div>`;
}

function seccionInstitucionesHTML() {
  const s = state.admin;
  return `<div class="flex flex-col gap-6">
    ${card("Pagos pendientes de validación", s.pagos.length === 0 ? `<p class="text-xs text-slate-400">No hay pagos pendientes.</p>` : `<div class="flex flex-col gap-2">${s.pagos.map((p) => `
      <div class="flex items-center gap-3 text-xs border border-slate-100 rounded-lg px-3 py-2"><span class="flex-1"><b>${esc(state.nombres[p.equipo_id] || "Equipo #" + p.equipo_id)}</b> · $${Number(p.monto).toLocaleString("es-CO")} · ${esc(p.metodo_pago)} ${p.referencia_transaccion ? "· ref. " + esc(p.referencia_transaccion) : ""} ${p.comprobante_url ? `· <a class="underline text-blue-900" target="_blank" rel="noopener noreferrer" href="${esc(p.comprobante_url)}">comprobante</a>` : ""}</span>
      <button data-action="pago-aprobar" data-id="${p.id}" class="${BTN}">Aprobar</button><button data-action="pago-rechazar" data-id="${p.id}" class="text-xs font-bold text-red-600 border border-red-200 px-3 py-2 rounded-lg hover:bg-red-50">Rechazar</button></div>`).join("")}</div>`)}
    <div class="bg-white rounded-xl shadow-sm overflow-hidden"><div class="px-5 py-4 border-b border-slate-100"><h3 class="text-sm font-bold text-blue-950">Equipos del torneo seleccionado</h3></div>
      <div class="overflow-x-auto"><table class="w-full text-xs"><thead><tr class="text-slate-400 border-b border-slate-100"><th class="py-2.5 px-4 text-left font-medium">EQUIPO</th><th class="py-2.5 px-3 text-left font-medium">COLEGIO</th>${TH("INSCRIPCIÓN", 3)}${TH("ACCIONES", 4)}</tr></thead><tbody>
        ${s.equipos.length === 0 ? `<tr><td colspan="4" class="py-8 text-center text-slate-400">Sin equipos inscritos.</td></tr>` : ""}
        ${s.equipos.map((e) => { const c = porId(s.colegios, e.colegio_id); return `<tr class="border-b border-slate-50 last:border-0"><td class="py-2.5 px-4 font-medium text-slate-700">${esc(e.nombre)}</td><td class="py-2.5 px-3 text-slate-500">${esc(c ? c.nombre : "#" + e.colegio_id)}</td>
          <td class="py-2.5 px-3 text-center"><span class="px-2.5 py-1 rounded-full text-[10.5px] font-bold ${BADGE_INSCRIPCION[e.estado_inscripcion] || ""}">${esc(e.estado_inscripcion.replace("_", " "))}</span></td>
          <td class="py-2.5 px-4 text-center">${e.estado_inscripcion !== "Descalificado" ? `<button data-action="descalificar" data-id="${e.id}" class="text-[11px] font-semibold text-red-600 underline underline-offset-2">Descalificar</button>` : ""}</td></tr>`; }).join("")}
      </tbody></table></div></div>
    ${card("Registrar colegio", `<form id="form-colegio"><div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
      ${campo("Nombre", entrada("nombre", "", "required"))}${campo("Dirección", entrada("direccion", "", "required"))}${campo("Representante legal", entrada("representante_legal", "", "required"))}
      ${campo("Teléfono", entrada("telefono_contacto", "", "required"))}${campo("Correo institucional (opcional)", entrada("email_institucional", "", 'type="email"'))}</div><button type="submit" class="${BTN} mt-4">+ Registrar colegio</button></form>`)}
    <div class="bg-white rounded-xl shadow-sm overflow-hidden"><div class="px-5 py-4 border-b border-slate-100"><h3 class="text-sm font-bold text-blue-950">Colegios</h3></div>
      ${s.colegios.map((c) => `<div class="flex items-center gap-3 px-5 py-2.5 border-b border-slate-50 last:border-0 text-xs"><span class="flex-1 font-medium text-slate-700">${esc(c.nombre)}</span><span class="text-slate-400">${esc(c.representante_legal)}</span>
        <button data-action="toggle-colegio" data-id="${c.id}" class="font-semibold text-blue-900 underline underline-offset-2">${c.estado_activo ? "Desactivar" : "Activar"}</button></div>`).join("") || `<p class="p-5 text-xs text-slate-400">Sin colegios.</p>`}</div></div>`;
}

function seccionUsuariosHTML() {
  const s = state.admin;
  return `<div class="flex flex-col gap-6">
    ${card("Crear cuenta", `<form id="form-usuario"><div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
      ${campo("Rol", `<select name="rol" class="${INPUT}"><option>Entrenador</option><option>Arbitro</option><option>Administrador</option></select>`)}
      ${campo("Nombre completo", entrada("nombre_completo", "", "required"))}${campo("Correo", entrada("email", "", 'type="email" required'))}
      ${campo("Teléfono", entrada("telefono_contacto", "", "required"))}${campo("Contraseña (8-72)", entrada("password", "", 'type="password" minlength="8" maxlength="72" required'))}
      ${campo("Colegio (solo entrenadores)", `<select name="colegio_id" class="${INPUT}"><option value="">Sin colegio</option>${s.colegios.filter((c) => c.estado_activo).map((c) => `<option value="${c.id}">${esc(c.nombre)}</option>`).join("")}</select>`)}</div>
      <button type="submit" class="${BTN} mt-4">+ Crear cuenta</button></form>`)}
    <div class="bg-white rounded-xl shadow-sm overflow-hidden"><div class="px-5 py-4 border-b border-slate-100"><h3 class="text-sm font-bold text-blue-950">Cuentas</h3></div>
      ${s.usuarios.map((u) => `<div class="flex items-center gap-3 px-5 py-2.5 border-b border-slate-50 last:border-0 text-xs"><span class="flex-1 font-medium text-slate-700">${esc(u.nombre_completo)}<span class="block text-[11px] font-normal text-slate-400">${esc(u.email)}</span></span><span class="text-slate-500">${esc(u.rol)}</span>
        <button data-action="toggle-usuario" data-id="${u.id}" class="font-semibold ${u.estado_activo ? "text-red-600" : "text-emerald-700"} underline underline-offset-2">${u.estado_activo ? "Suspender" : "Reactivar"}</button></div>`).join("")}</div></div>`;
}

/* ============================================================
   11. ACCIONES
   ============================================================ */
async function handleAction(action, el) {
  const d = state.dash, a = state.arb, c = state.coach, s = state.admin;
  const recargar = async (fn) => { await fn(); render(); };

  /* ----- sesión ----- */
  if (action === "abrir-login") { state.loginModal = true; render(); return; }
  if (action === "cerrar-login") { state.loginModal = false; render(); return; }
  if (action === "cerrar-sesion") { cerrarSesion(true); return; }

  /* ----- dashboard ----- */
  if (action === "dashboard-tab") { d.tab = el.dataset.tab; render(); return; }
  if (action === "dash-torneo") { d.torneoId = Number(el.value); d.faseId = null; await cargarVista(); return; }
  if (action === "dash-fase") { d.faseId = Number(el.value); await cargarVista(); return; }

  /* ----- árbitro ----- */
  if (action === "select-partido") { a.id = Number(el.value); state.cargando = true; render(); await intentar(cargarDetallePartido); state.cargando = false; render(); return; }
  if (action === "iniciar-partido") {
    await intentar(async () => { await POST(`/partidos/${a.id}/iniciar`); await recargarPartidoArbitro(); mostrarToast("Partido iniciado."); });
    render(); return;
  }
  if (action === "toggle-timer") {
    a.running = !a.running; clearInterval(a.timerId);
    if (a.running) a.timerId = setInterval(() => { a.seconds++; const r = document.getElementById("reloj"); if (r) r.textContent = formatoReloj(a.seconds); }, 1000);
    render(); return;
  }
  if (action === "abrir-modal") { a.modal = { tipo: el.dataset.tipo, equipo: el.dataset.equipo, sale: null }; render(); return; }
  if (action === "cerrar-modal") { a.modal = null; render(); return; }
  if (action === "registrar-evento") {
    const modal = a.modal, jugadorId = Number(el.dataset.jugadorId), equipoId = Number(el.dataset.equipoId);
    if (modal.tipo === "Sustitucion" && !modal.sale) { modal.sale = jugadorId; render(); return; }
    const cuerpo = { equipo_id: equipoId, jugador_id: jugadorId, tipo_evento: modal.tipo, minuto_ocurrencia: Math.min(150, Math.floor(a.seconds / 60)) };
    if (modal.tipo === "Sustitucion") cuerpo.jugador_secundario_id = modal.sale;
    await intentar(async () => { await POST(`/partidos/${a.id}/eventos`, cuerpo); a.modal = null; await recargarPartidoArbitro(); });
    render(); return;
  }
  if (action === "eliminar-evento") {
    await intentar(async () => { await DELETE(`/partidos/${a.id}/eventos/${el.dataset.eventoId}`); await recargarPartidoArbitro(); });
    render(); return;
  }
  if (action === "finalizar-partido") {
    if (!confirm("¿Cerrar el acta? Después de cerrarla el marcador ya no se puede modificar.")) return;
    await intentar(async () => { await POST(`/partidos/${a.id}/cerrar`); clearInterval(a.timerId); a.running = false; await recargarPartidoArbitro(); mostrarToast("Acta cerrada: tabla de posiciones actualizada."); });
    render(); return;
  }

  /* ----- entrenador ----- */
  if (action === "select-equipo") { c.equipoId = Number(el.value); state.cargando = true; render(); await intentar(cargarDetalleEquipo); state.cargando = false; render(); return; }
  if (action === "toggle-form-equipo") { c.showEquipo = !c.showEquipo; render(); return; }
  if (action === "abrir-pago-modal") { c.showPago = true; render(); return; }
  if (action === "cerrar-pago-modal") { c.showPago = false; render(); return; }
  if (action === "eliminar-jugador") {
    if (!confirm("¿Dar de baja a este jugador?")) return;
    await intentar(async () => { await POST(`/jugadores/${el.dataset.jugadorId}/baja`); await cargarDetalleEquipo(); mostrarToast("Jugador dado de baja.", "info"); });
    render(); return;
  }
  if (action === "abrir-planilla") {
    const roles = {};
    c.jugadores.forEach((j) => { roles[j.id] = "no"; });
    c.planilla = { partidoId: Number(el.dataset.partidoId), roles }; render(); return;
  }
  if (action === "cerrar-planilla") { c.planilla = null; render(); return; }

  /* ----- admin: navegación ----- */
  if (action === "admin-section") { s.section = el.dataset.section; render(); return; }
  if (action === "admin-torneo") { s.torneoId = Number(el.value); await intentar(async () => { await cargarTorneoAdmin(); }); render(); return; }
  if (action === "admin-fase") { s.faseId = Number(el.value); await intentar(cargarFaseAdmin); render(); return; }

  /* ----- admin: torneos ----- */
  const rutasTorneo = { "torneo-iniciar": "iniciar", "torneo-finalizar": "finalizar", "torneo-cancelar": "cancelar" };
  if (rutasTorneo[action]) {
    if (action !== "torneo-iniciar" && !confirm("¿Confirmas la acción sobre el torneo?")) return;
    await intentar(async () => { await POST(`/torneos/${s.torneoId}/${rutasTorneo[action]}`); mostrarToast("Estado del torneo actualizado."); await recargarAdmin(); });
    return;
  }

  /* ----- admin: fixtures ----- */
  if (action === "generar-fixture") {
    const chk = document.getElementById("chk-arbitros");
    await intentar(async () => { const r = await POST(`/fases/${s.faseId}/fixture`, { asignar_arbitros: !!(chk && chk.checked) }); mostrarToast(`${r.length} partido(s) programado(s).`); await cargarFaseAdmin(); });
    render(); return;
  }
  if (action === "reprogramar") {
    const p = porId(s.partidos, el.dataset.id);
    let fecha = fechaDe(p.fecha_hora), hora = horaDe(p.fecha_hora), cancha = p.cancha_id;
    if (el.dataset.campo === "fecha") fecha = el.value; else if (el.dataset.campo === "hora") hora = el.value; else cancha = Number(el.value);
    await intentar(async () => { await PATCH(`/partidos/${p.id}/reprogramar`, { fecha_hora: `${fecha}T${hora}:00`, cancha_id: cancha }); mostrarToast("Partido reprogramado."); });
    await intentar(cargarFaseAdmin); render(); return;
  }
  if (action === "asignar-arbitro") {
    if (!el.value) return;
    await intentar(async () => { await PUT(`/partidos/${el.dataset.id}/arbitro`, { arbitro_id: Number(el.value) }); mostrarToast("Árbitro asignado."); });
    await intentar(cargarFaseAdmin); render(); return;
  }
  if (action === "suspender-partido") { await intentar(async () => { await POST(`/partidos/${el.dataset.id}/suspender`); mostrarToast("Partido suspendido.", "info"); }); await intentar(cargarFaseAdmin); render(); return; }
  if (action === "walkover") {
    const p = porId(s.partidos, el.dataset.id);
    const local = confirm(`W.O.: Aceptar = gana ${nombreEquipo(p.equipo_local_id)}; Cancelar = elegir ${nombreEquipo(p.equipo_visitante_id)}.`);
    const ganador = local ? p.equipo_local_id : p.equipo_visitante_id;
    if (!confirm(`¿Decretar W.O. a favor de ${nombreEquipo(ganador)}?`)) return;
    await intentar(async () => { await POST(`/partidos/${p.id}/walkover`, { equipo_ganador_id: ganador }); mostrarToast("W.O. decretado."); });
    await intentar(cargarFaseAdmin); render(); return;
  }
  if (action === "cerrar-grupo") { await intentar(async () => { await POST(`/tablas/${el.dataset.tablaId}/cerrar`); mostrarToast("Grupo cerrado."); }); await intentar(cargarFaseAdmin); render(); return; }
  if (action === "cerrar-fase") { await intentar(async () => { await POST(`/fases/${s.faseId}/cerrar`); mostrarToast("Fase finalizada."); await cargarTorneoAdmin(); }); render(); return; }

  /* ----- admin: sedes, colegios, pagos, cuentas ----- */
  if (action === "toggle-cancha") { const x = porId(s.canchas, el.dataset.id); await intentar(async () => { await PATCH(`/canchas/${x.id}/estado`, { estado_activo: !x.estado_activo }); await recargarAdmin(); }); return; }
  if (action === "toggle-colegio") { const x = porId(s.colegios, el.dataset.id); await intentar(async () => { await PATCH(`/colegios/${x.id}`, { estado_activo: !x.estado_activo }); await recargarAdmin(); }); return; }
  if (action === "toggle-usuario") { const x = porId(s.usuarios, el.dataset.id); await intentar(async () => { await PATCH(`/usuarios/${x.id}/estado`, { estado_activo: !x.estado_activo }); await recargarAdmin(); }); return; }
  if (action === "pago-aprobar") { await intentar(async () => { await PATCH(`/pagos/${el.dataset.id}/validar`, { aprobado: true }); mostrarToast("Pago aprobado: equipo habilitado."); await recargarAdmin(); }); return; }
  if (action === "pago-rechazar") {
    const motivo = (prompt("Motivo del rechazo (obligatorio):") || "").trim();
    if (!motivo) { mostrarToast("El rechazo necesita un motivo.", "error"); return; }
    await intentar(async () => { await PATCH(`/pagos/${el.dataset.id}/validar`, { aprobado: false, observaciones: motivo }); mostrarToast("Pago rechazado.", "info"); await recargarAdmin(); });
    return;
  }
  if (action === "descalificar") {
    if (!confirm("¿Descalificar este equipo?")) return;
    await intentar(async () => { await POST(`/equipos/${el.dataset.id}/descalificar`); await recargarAdmin(); });
    return;
  }
}

/* ============================================================
   12. FORMULARIOS Y DELEGACIÓN DE EVENTOS
   ============================================================ */
const textoOnull = (v) => { const t = String(v ?? "").trim(); return t === "" ? null : t; };
const enteroOnull = (v) => (String(v ?? "").trim() === "" ? null : Number(v));

async function enviarFormulario(id, f) {
  const c = state.coach, s = state.admin;
  if (id === "form-login") { await iniciarSesion(f.email.trim(), f.password); return; }

  if (id === "form-equipo") {
    const nuevo = await POST("/equipos/", { colegio_id: Number(f.colegio_id), torneo_id: Number(f.torneo_id), nombre: f.nombre.trim() });
    c.showEquipo = false; c.equipoId = nuevo.id; mostrarToast("Equipo inscrito. Agrega jugadores y reporta el pago."); await cargarCoach(); render(); return;
  }
  if (id === "form-jugador") {
    await POST(`/equipos/${c.equipoId}/jugadores`, {
      nombre_completo: f.nombre_completo.trim(), identificacion: f.identificacion.trim(), fecha_nacimiento: f.fecha_nacimiento,
      numero_camiseta: enteroOnull(f.numero_camiseta), posicion: textoOnull(f.posicion),
    });
    mostrarToast("Jugador inscrito."); await cargarDetalleEquipo(); render(); return;
  }
  if (id === "form-pago") {
    await POST(`/equipos/${c.equipoId}/pagos`, { monto: String(f.monto), metodo_pago: f.metodo_pago, referencia_transaccion: textoOnull(f.referencia_transaccion), comprobante_url: textoOnull(f.comprobante_url) });
    c.showPago = false; mostrarToast("Pago reportado: queda pendiente de validación."); await cargarCoach(); render(); return;
  }
  if (id === "form-planilla") {
    const jugadores = c.jugadores.filter((j) => c.planilla.roles[j.id] !== "no").map((j) => ({ jugador_id: j.id, es_titular: c.planilla.roles[j.id] === "titular" }));
    await PUT(`/partidos/${c.planilla.partidoId}/equipos/${c.equipoId}/alineacion`, { jugadores });
    c.planilla = null; mostrarToast("Planilla enviada."); render(); return;
  }

  if (id === "form-torneo") {
    const reglas = { min_jugadores: Number(f.min_jugadores), max_jugadores: Number(f.max_jugadores), min_equipos: Number(f.min_equipos), titulares: Number(f.titulares), max_suplentes: Number(f.max_suplentes) };
    const t = await POST("/torneos/", { nombre: f.nombre.trim(), categoria: f.categoria.trim(), fecha_inicio: f.fecha_inicio, fecha_fin: f.fecha_fin, reglas });
    s.torneoId = t.id; mostrarToast("Torneo creado."); await recargarAdmin(); return;
  }
  if (id === "form-fase") { await POST(`/torneos/${s.torneoId}/fases`, { nombre: f.nombre.trim(), tipo_formato: f.tipo_formato }); mostrarToast("Fase agregada."); await recargarAdmin(); return; }
  if (id === "form-grupos") {
    const n = Number(f.n), hab = s.equipos.filter((e) => e.estado_inscripcion === "Habilitado").map((e) => e.id);
    if (hab.length < n * 2) { mostrarToast(`Con ${hab.length} equipos habilitados no se pueden armar ${n} grupos de al menos 2.`, "error"); return; }
    const grupos = {};
    hab.forEach((eid, i) => { const nombre = "Grupo " + String.fromCharCode(65 + (i % n)); (grupos[nombre] = grupos[nombre] || []).push(eid); });
    await POST(`/fases/${s.faseId}/grupos`, { grupos }); mostrarToast("Grupos creados."); await cargarFaseAdmin(); render(); return;
  }
  if (id === "form-cancha") { await POST("/canchas/", { nombre: f.nombre.trim(), direccion_sede: f.direccion_sede.trim(), tipo_superficie: f.tipo_superficie }); mostrarToast("Sede registrada."); await recargarAdmin(); return; }
  if (id === "form-colegio") {
    await POST("/colegios/", { nombre: f.nombre.trim(), direccion: f.direccion.trim(), representante_legal: f.representante_legal.trim(), telefono_contacto: f.telefono_contacto.trim(), email_institucional: textoOnull(f.email_institucional) });
    mostrarToast("Colegio registrado."); await recargarAdmin(); return;
  }
  if (id === "form-usuario") {
    const cuerpo = { rol: f.rol, nombre_completo: f.nombre_completo.trim(), email: f.email.trim(), telefono_contacto: f.telefono_contacto.trim(), password: f.password };
    if (f.rol === "Entrenador" && f.colegio_id) cuerpo.colegio_id = Number(f.colegio_id);
    await POST("/usuarios/", cuerpo); mostrarToast("Cuenta creada."); await recargarAdmin(); return;
  }
}

document.addEventListener("click", (e) => {
  const nav = e.target.closest("[data-nav]");
  if (nav) { setView(nav.dataset.nav); return; }
  const el = e.target.closest("[data-action]");
  if (el && !["SELECT", "INPUT"].includes(el.tagName)) intentar(() => handleAction(el.dataset.action, el));
});
document.addEventListener("change", (e) => {
  if (e.target.dataset.role === "rol-jugador") {
    state.coach.planilla.roles[e.target.dataset.jugadorId] = e.target.value;
    const cuenta = (v) => Object.values(state.coach.planilla.roles).filter((x) => x === v).length;
    const n = document.getElementById("conteo-planilla"); if (n) n.textContent = `${cuenta("titular")} titulares, ${cuenta("suplente")} suplentes`;
    return;
  }
  const el = e.target.closest("[data-action]");
  if (el && ["SELECT", "INPUT"].includes(el.tagName)) intentar(() => handleAction(el.dataset.action, el));
});
document.addEventListener("submit", (e) => {
  if (!e.target.id || !e.target.id.startsWith("form-")) return;
  e.preventDefault();
  const datos = Object.fromEntries(new FormData(e.target).entries());
  const boton = e.target.querySelector('[type="submit"]');
  if (boton) boton.disabled = true;
  intentar(() => enviarFormulario(e.target.id, datos)).finally(() => { if (boton && document.body.contains(boton)) boton.disabled = false; });
});

/* ============================================================
   13. INICIO
   ============================================================ */
cargarVista();
