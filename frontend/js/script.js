/* ============================================================
   1. MOCK DATA — INITIAL_MOCK_DATA
   ============================================================ */
const INITIAL_MOCK_DATA = {
  torneos: [
    { id: "t1", nombre: "Copa Intercolegiada 2026", categoria: "Sub-15", fase: "Fase de Grupos" },
    { id: "t2", nombre: "Copa Intercolegiada 2026", categoria: "Sub-17", fase: "Fase de Grupos" },
  ],
  colegios: [
    { id: "c1", nombre: "Colegio San José", sigla: "SJ", escudoSimulado: "🛡️", estadoInscripcion: "VALIDADO" },
    { id: "c2", nombre: "Gimnasio del Norte", sigla: "GN", escudoSimulado: "🛡️", estadoInscripcion: "VALIDADO" },
    { id: "c3", nombre: "I.E. Simón Bolívar", sigla: "ISB", escudoSimulado: "🛡️", estadoInscripcion: "VALIDADO" },
    { id: "c4", nombre: "Liceo La Salle", sigla: "LLS", escudoSimulado: "🛡️", estadoInscripcion: "VALIDADO" },
    { id: "c5", nombre: "Instituto Nuestra Señora", sigla: "INS", escudoSimulado: "🛡️", estadoInscripcion: "PENDIENTE" },
    { id: "c6", nombre: "Colegio Biffi", sigla: "CB", escudoSimulado: "🛡️", estadoInscripcion: "VALIDADO" },
  ],
  jugadores: [
    { id: "j1", colegioId: "c1", nombre: "Carlos Romero", documento: "1098234001", camiseta: 10, posicion: "Delantero", pazYSalvo: true },
    { id: "j2", colegioId: "c1", nombre: "Samuel Arrieta", documento: "1098234002", camiseta: 7, posicion: "Delantero", pazYSalvo: true },
    { id: "j3", colegioId: "c1", nombre: "Mateo Salcedo", documento: "1098234003", camiseta: 1, posicion: "Portero", pazYSalvo: true },
    { id: "j4", colegioId: "c2", nombre: "Andrés Pérez", documento: "1098234004", camiseta: 9, posicion: "Delantero", pazYSalvo: true },
    { id: "j5", colegioId: "c2", nombre: "Kevin Julio", documento: "1098234005", camiseta: 5, posicion: "Defensa", pazYSalvo: true },
    { id: "j6", colegioId: "c3", nombre: "Juan Pablo Díaz", documento: "1098234006", camiseta: 9, posicion: "Delantero", pazYSalvo: true },
    { id: "j7", colegioId: "c3", nombre: "Luis Fernández", documento: "1098234007", camiseta: 4, posicion: "Defensa", pazYSalvo: true },
    { id: "j8", colegioId: "c4", nombre: "Miguel Torres", documento: "1098234008", camiseta: 11, posicion: "Delantero", pazYSalvo: true },
    { id: "j9", colegioId: "c4", nombre: "Jorge Ramos", documento: "1098234009", camiseta: 6, posicion: "Mediocampo", pazYSalvo: false },
    { id: "j10", colegioId: "c5", nombre: "David Contreras", documento: "1098234010", camiseta: 8, posicion: "Mediocampo", pazYSalvo: true },
    { id: "j11", colegioId: "c6", nombre: "Sebastián Márquez", documento: "1098234011", camiseta: 10, posicion: "Delantero", pazYSalvo: true },
    { id: "j12", colegioId: "c6", nombre: "Camilo Reyes", documento: "1098234012", camiseta: 2, posicion: "Defensa", pazYSalvo: true },
  ],
  sedes: [
    { id: "s1", nombre: "Cancha 1 — Complejo Turbaco", direccion: "Cra 5 #12-30, Turbaco", tipoSuperficie: "Sintética" },
    { id: "s2", nombre: "Cancha 2 — Polideportivo Central", direccion: "Av. Pedro de Heredia #45-10", tipoSuperficie: "Cemento" },
    { id: "s3", nombre: "Cancha 3 — IED Bicentenario", direccion: "Calle 8 #22-15, Cartagena", tipoSuperficie: "Sintética" },
  ],
  partidos: [
    { id: "p1", torneoId: "t1", local: { colegioId: "c1", marcador: 2 }, visitante: { colegioId: "c3", marcador: 1 },
      fecha: "2026-09-21", hora: "15:00", minutoActual: 34, tiempo: "Tiempo 1", sedeId: "s1", estado: "EN_VIVO",
      eventos: [
        { id: "e1", minuto: 12, tipo: "GOL", jugadorId: "j1", colegioId: "c1" },
        { id: "e2", minuto: 21, tipo: "TARJETA_AMARILLA", jugadorId: "j7", colegioId: "c3" },
        { id: "e3", minuto: 29, tipo: "GOL", jugadorId: "j6", colegioId: "c3" },
        { id: "e4", minuto: 33, tipo: "GOL", jugadorId: "j2", colegioId: "c1" },
      ] },
    { id: "p2", torneoId: "t1", local: { colegioId: "c4", marcador: 0 }, visitante: { colegioId: "c2", marcador: 0 },
      fecha: "2026-09-21", hora: "17:00", minutoActual: 0, tiempo: "Tiempo 1", sedeId: "s2", estado: "PROGRAMADO", eventos: [] },
    { id: "p3", torneoId: "t1", local: { colegioId: "c5", marcador: 1 }, visitante: { colegioId: "c6", marcador: 3 },
      fecha: "2026-09-14", hora: "16:00", minutoActual: 90, tiempo: "Tiempo 2", sedeId: "s3", estado: "FINALIZADO",
      eventos: [
        { id: "e5", minuto: 15, tipo: "GOL", jugadorId: "j11", colegioId: "c6" },
        { id: "e6", minuto: 40, tipo: "GOL", jugadorId: "j11", colegioId: "c6" },
        { id: "e7", minuto: 58, tipo: "GOL", jugadorId: "j10", colegioId: "c5" },
        { id: "e8", minuto: 77, tipo: "GOL", jugadorId: "j11", colegioId: "c6" },
      ] },
    { id: "p4", torneoId: "t1", local: { colegioId: "c1", marcador: null }, visitante: { colegioId: "c4", marcador: null },
      fecha: "2026-09-28", hora: "09:00", minutoActual: 0, tiempo: "Tiempo 1", sedeId: "s1", estado: "PROGRAMADO", eventos: [] },
  ],
};

const EVENT_META = {
  GOL: { label: "Gol", icon: "⚽", bg: "bg-emerald-50" },
  TARJETA_AMARILLA: { label: "Tarjeta amarilla", icon: "🟨", bg: "bg-amber-50" },
  TARJETA_ROJA: { label: "Tarjeta roja", icon: "🟥", bg: "bg-red-50" },
};
const POSICIONES = ["Portero", "Defensa", "Mediocampo", "Delantero"];
const POSICION_COLOR = {
  Portero: "bg-purple-100 text-purple-700",
  Defensa: "bg-blue-100 text-blue-700",
  Mediocampo: "bg-amber-100 text-amber-700",
  Delantero: "bg-emerald-100 text-emerald-700",
};
const CUPO_MAXIMO = 18;
const ADMIN_SECTIONS = [
  { id: "TORNEOS", label: "Torneos y Categorías" },
  { id: "FIXTURES", label: "Generador de Fixtures" },
  { id: "SEDES", label: "Gestión de Sedes y Canchas" },
  { id: "INSTITUCIONES", label: "Control de Instituciones" },
];
const SUPERFICIES = ["Sintética", "Grama", "Cemento", "Coliseo"];
const ESTADOS_PARTIDO = ["PROGRAMADO", "EN_VIVO", "FINALIZADO"];
const NAV_ITEMS = [
  { id: "DASHBOARD_PUBLICO", label: "Dashboard Público", icon: "trophy" },
  { id: "PLANILLA_ARBITRO", label: "Planilla Árbitro", icon: "clipboard-list" },
  { id: "PANEL_COACH", label: "Panel Coach", icon: "shield-check" },
  { id: "PANEL_ADMIN", label: "Panel Admin", icon: "settings-2" },
];

/* ============================================================
   2. ESTADO GLOBAL
   ============================================================ */
const state = {
  view: "DASHBOARD_PUBLICO",
  data: JSON.parse(JSON.stringify(INITIAL_MOCK_DATA)),
  dashboard: { categoria: "Sub-15", fase: "Fase de Grupos", tab: "POSICIONES" },
  arbitro: { selectedPartidoId: null, seconds: 0, running: false, timerId: null, modal: null },
  coach: { selectedColegioId: "c2", showPagoModal: false, editingId: null, editDraft: { camiseta: "", posicion: "" } },
  admin: { section: "FIXTURES", categoria: "Sub-15", sistema: "Fase de Grupos" },
  toast: null,
  toastTimer: null,
};
(function initArbitro(){
  const enVivo = state.data.partidos.find((p) => p.estado === "EN_VIVO");
  const disponible = enVivo || state.data.partidos.find((p) => p.estado === "PROGRAMADO");
  state.arbitro.selectedPartidoId = disponible ? disponible.id : null;
  if (disponible) state.arbitro.seconds = (disponible.minutoActual || 0) * 60;
})();

/* ============================================================
   3. HELPERS
   ============================================================ */
function getColegio(id) { return state.data.colegios.find((c) => c.id === id); }
function getJugador(id) { return state.data.jugadores.find((j) => j.id === id); }
function esc(s) { return String(s ?? "").replace(/[&<>"']/g, (m) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[m])); }

function computeStandings(data) {
  const stats = {};
  data.colegios.forEach((c) => { stats[c.id] = { colegioId: c.id, pj: 0, pg: 0, pe: 0, pp: 0, gf: 0, gc: 0, pts: 0 }; });
  data.partidos.filter((p) => p.estado === "FINALIZADO").forEach((p) => {
    const localId = p.local.colegioId, visId = p.visitante.colegioId;
    const gfLocal = p.local.marcador ?? 0, gfVis = p.visitante.marcador ?? 0;
    if (!stats[localId] || !stats[visId]) return;
    stats[localId].pj++; stats[visId].pj++;
    stats[localId].gf += gfLocal; stats[localId].gc += gfVis;
    stats[visId].gf += gfVis; stats[visId].gc += gfLocal;
    if (gfLocal > gfVis) { stats[localId].pg++; stats[localId].pts += 3; stats[visId].pp++; }
    else if (gfLocal < gfVis) { stats[visId].pg++; stats[visId].pts += 3; stats[localId].pp++; }
    else { stats[localId].pe++; stats[visId].pe++; stats[localId].pts++; stats[visId].pts++; }
  });
  return Object.values(stats)
    .map((s) => ({ ...s, dg: s.gf - s.gc }))
    .sort((a, b) => b.pts - a.pts || b.dg - a.dg || b.gf - a.gf)
    .map((s, idx) => ({ ...s, pos: idx + 1 }));
}
function computeGoleadores(data) {
  const conteo = {};
  data.partidos.forEach((p) => p.eventos.forEach((e) => { if (e.tipo === "GOL") conteo[e.jugadorId] = (conteo[e.jugadorId] || 0) + 1; }));
  return Object.entries(conteo)
    .map(([jugadorId, goles]) => { const j = data.jugadores.find((x) => x.id === jugadorId); return { jugadorId, colegioId: j?.colegioId, goles }; })
    .sort((a, b) => b.goles - a.goles).slice(0, 5);
}
function setPath(obj, path, value) {
  const keys = path.split(".");
  let o = obj;
  for (let i = 0; i < keys.length - 1; i++) o = o[keys[i]];
  o[keys[keys.length - 1]] = value;
}
function getPath(obj, path) {
  return path.split(".").reduce((o, k) => (o ? o[k] : undefined), obj);
}

/* ============================================================
   4. RENDER RAÍZ
   ============================================================ */
function render() {
  document.getElementById("header").innerHTML = renderHeader();
  const main = document.getElementById("main");
  if (state.view === "DASHBOARD_PUBLICO") main.innerHTML = renderDashboard();
  else if (state.view === "PLANILLA_ARBITRO") main.innerHTML = renderArbitro();
  else if (state.view === "PANEL_COACH") main.innerHTML = renderCoach();
  else if (state.view === "PANEL_ADMIN") main.innerHTML = renderAdmin();
  if (window.lucide) lucide.createIcons();
}
function renderToast() {
  document.getElementById("toast-root").innerHTML = state.toast ? toastHTML(state.toast.message, state.toast.type) : "";
  if (window.lucide) lucide.createIcons();
}
function mostrarToast(message, type) {
  state.toast = { message, type: type || "success" };
  renderToast();
  clearTimeout(state.toastTimer);
  state.toastTimer = setTimeout(() => { state.toast = null; renderToast(); }, 3000);
}
function toastHTML(message, type) {
  const styles = { success: "bg-emerald-600", error: "bg-red-600", info: "bg-blue-950" };
  const icon = type === "error" ? "alert-circle" : type === "info" ? "" : "check-circle-2";
  return `
  <div class="fixed top-4 left-1/2 -translate-x-1/2 z-[60] px-4">
    <div class="flex items-center gap-2 text-white text-xs font-semibold px-4 py-2.5 rounded-lg shadow-lg ${styles[type] || styles.success}">
      ${icon ? `<i data-lucide="${icon}" class="w-3.5 h-3.5"></i>` : ""} ${esc(message)}
    </div>
  </div>`;
}

function setView(v) {
  if (state.view === "PLANILLA_ARBITRO" && v !== "PLANILLA_ARBITRO") { clearInterval(state.arbitro.timerId); state.arbitro.running = false; }
  state.view = v;
  render();
}

/* ============================================================
   5. HEADER
   ============================================================ */
function renderHeader() {
  return `
  <header class="sticky top-0 z-40 bg-blue-950 shadow-sm">
    <div class="mx-auto max-w-6xl px-4 py-3 flex items-center justify-between gap-4">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-lg bg-emerald-600 flex items-center justify-center text-white font-bold text-sm">CI</div>
        <div class="leading-tight">
          <p class="text-white font-semibold text-sm">Copa Intercolegiada 2026</p>
          <p class="text-blue-200/70 text-xs">Cartagena · Torneo Intercolegiado</p>
        </div>
      </div>
      <nav class="flex items-center gap-1 overflow-x-auto">
        ${NAV_ITEMS.map((n) => `
          <button data-nav="${n.id}" class="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium whitespace-nowrap transition-colors ${state.view === n.id ? "bg-white text-blue-950" : "text-blue-200/80 hover:bg-white/10 hover:text-white"}">
            <i data-lucide="${n.icon}" class="w-3.5 h-3.5"></i>${n.label}
          </button>`).join("")}
      </nav>
    </div>
  </header>`;
}

/* ============================================================
   6. HELPERS DE UI COMPARTIDOS
   ============================================================ */
function filterDropdown(bindPath, value, options, renderLabelFn, action) {
  return `
  <div class="relative">
    <select ${action ? `data-action="${action}"` : `data-bind="${bindPath}"`} class="appearance-none bg-white border border-slate-200 rounded-lg pl-3 pr-8 py-2 text-xs font-medium text-blue-900 shadow-sm cursor-pointer focus:outline-none focus:ring-2 focus:ring-emerald-600">
      ${options.map((opt) => `<option value="${esc(opt)}" ${opt === value ? "selected" : ""}>${esc(renderLabelFn ? renderLabelFn(opt) : opt)}</option>`).join("")}
    </select>
    <i data-lucide="chevron-down" class="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 w-3.5 h-3.5"></i>
  </div>`;
}

/* ============================================================
   7. PANTALLA 1 — DASHBOARD PÚBLICO
   ============================================================ */
function renderDashboard() {
  const d = state.dashboard;
  const tabla = computeStandings(state.data);
  const goleadores = computeGoleadores(state.data);
  const destacado = state.data.partidos.find((p) => p.estado === "EN_VIVO") || state.data.partidos.find((p) => p.estado === "PROGRAMADO");
  const sede = destacado ? state.data.sedes.find((s) => s.id === destacado.sedeId) : null;

  return `
  <div class="min-h-screen bg-slate-50">
    <div class="mx-auto max-w-6xl px-4 pt-6 flex flex-wrap gap-3">
      ${filterDropdown("dashboard.categoria", d.categoria, ["Sub-15", "Sub-17"], (o) => "Categoría: " + o)}
      ${filterDropdown("dashboard.fase", d.fase, ["Fase de Grupos", "Eliminación Directa"], (o) => "Fase: " + o)}
    </div>
    <div class="mx-auto max-w-6xl px-4 py-6 grid grid-cols-1 lg:grid-cols-[2fr_1fr] gap-6 items-start">
      <div class="flex flex-col gap-6">
        ${destacado ? partidoDestacadoCard(destacado, sede) : ""}
        <div class="bg-white rounded-xl shadow-sm overflow-hidden">
          <div class="flex border-b border-slate-100">
            <button data-action="dashboard-tab" data-tab="POSICIONES" class="flex-1 py-3 text-xs font-semibold transition-colors ${d.tab === "POSICIONES" ? "text-emerald-700 border-b-2 border-emerald-600 bg-emerald-50/50" : "text-slate-400 hover:text-slate-600"}">Tabla General</button>
            <button data-action="dashboard-tab" data-tab="GOLEADORES" class="flex-1 py-3 text-xs font-semibold transition-colors ${d.tab === "GOLEADORES" ? "text-emerald-700 border-b-2 border-emerald-600 bg-emerald-50/50" : "text-slate-400 hover:text-slate-600"}">Líderes de Goleo</button>
          </div>
          ${d.tab === "POSICIONES" ? tablaPosicionesHTML(tabla) : tablaGoleadoresHTML(goleadores)}
        </div>
      </div>
      <aside class="bg-white rounded-xl shadow-sm p-4">
        <h3 class="text-sm font-semibold text-blue-950 mb-3">Próximos partidos</h3>
        <div class="flex flex-col gap-3">
          ${state.data.partidos.filter((p) => p.estado === "PROGRAMADO").map((p) => `
            <div class="flex items-center gap-2 text-xs text-slate-600">
              <i data-lucide="clock" class="w-3.5 h-3.5 text-slate-400 shrink-0"></i>
              <span class="flex-1">${esc(getColegio(p.local.colegioId)?.sigla)} vs ${esc(getColegio(p.visitante.colegioId)?.sigla)}</span>
              <span class="text-slate-400">${esc(p.hora)}</span>
            </div>`).join("")}
        </div>
      </aside>
    </div>
  </div>`;
}

function partidoDestacadoCard(partido, sede) {
  const local = getColegio(partido.local.colegioId), visitante = getColegio(partido.visitante.colegioId);
  const enVivo = partido.estado === "EN_VIVO";
  return `
  <div class="rounded-xl bg-blue-950 text-white p-5 shadow-sm">
    ${enVivo ? `
      <div class="inline-flex items-center gap-2 bg-emerald-600 text-white text-[11px] font-bold px-3 py-1 rounded-full mb-4">
        <span class="relative flex h-2 w-2"><span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-white/80 opacity-75"></span><span class="relative inline-flex rounded-full h-2 w-2 bg-white"></span></span>
        EN VIVO · ${partido.minutoActual}'
      </div>` : `<div class="inline-flex items-center gap-2 bg-white/10 text-blue-100 text-[11px] font-bold px-3 py-1 rounded-full mb-4">PRÓXIMO PARTIDO</div>`}
    <div class="flex items-center justify-between gap-4">
      <div class="flex-1 text-center"><div class="w-12 h-12 mx-auto mb-2 rounded-lg bg-white/10 flex items-center justify-center text-lg">${local?.escudoSimulado || ""}</div><p class="text-xs font-semibold leading-tight">${esc(local?.nombre)}</p></div>
      <div class="px-3 text-2xl font-extrabold tabular-nums">${partido.local.marcador ?? "-"}&nbsp;–&nbsp;${partido.visitante.marcador ?? "-"}</div>
      <div class="flex-1 text-center"><div class="w-12 h-12 mx-auto mb-2 rounded-lg bg-white/10 flex items-center justify-center text-lg">${visitante?.escudoSimulado || ""}</div><p class="text-xs font-semibold leading-tight">${esc(visitante?.nombre)}</p></div>
    </div>
    <div class="flex items-center justify-center gap-4 mt-4 text-[11px] text-blue-200/70">
      <span class="flex items-center gap-1"><i data-lucide="map-pin" class="w-3 h-3"></i>${esc(sede?.nombre)}</span>
      <span class="flex items-center gap-1"><i data-lucide="clock" class="w-3 h-3"></i>${esc(partido.hora)}</span>
    </div>
  </div>`;
}

function tablaPosicionesHTML(filas) {
  return `
  <div class="overflow-x-auto"><table class="w-full text-xs">
    <thead><tr class="text-slate-400 border-b border-slate-100">
      <th class="py-2.5 px-3 text-center font-medium">POS</th><th class="py-2.5 px-3 text-left font-medium">EQUIPO / COLEGIO</th>
      <th class="py-2.5 px-2 text-center font-medium">PJ</th><th class="py-2.5 px-2 text-center font-medium">PG</th>
      <th class="py-2.5 px-2 text-center font-medium">PE</th><th class="py-2.5 px-2 text-center font-medium">PP</th>
      <th class="py-2.5 px-2 text-center font-medium">GF</th><th class="py-2.5 px-2 text-center font-medium">GC</th>
      <th class="py-2.5 px-2 text-center font-medium">DG</th><th class="py-2.5 px-3 text-center font-medium">PTS</th>
    </tr></thead>
    <tbody>
      ${filas.length === 0 ? `<tr><td colspan="10" class="py-8 text-center text-slate-400">Aún no hay partidos finalizados para calcular la tabla.</td></tr>` : ""}
      ${filas.map((f) => { const c = getColegio(f.colegioId); const clas = f.pos <= 2; return `
      <tr class="border-b border-slate-50 last:border-0 ${clas ? "bg-emerald-50/60" : ""}">
        <td class="py-2.5 px-3 text-center"><span class="inline-flex items-center justify-center w-5 h-5 rounded text-[11px] font-bold ${clas ? "bg-emerald-600 text-white" : "bg-slate-100 text-slate-500"}">${f.pos}</span></td>
        <td class="py-2.5 px-3"><div class="flex items-center gap-2"><div class="w-6 h-6 rounded bg-blue-950 text-white flex items-center justify-center text-[9px] font-bold shrink-0">${esc(c?.sigla)}</div><span class="font-medium text-slate-700">${esc(c?.nombre)}</span></div></td>
        <td class="py-2.5 px-2 text-center text-slate-600">${f.pj}</td><td class="py-2.5 px-2 text-center text-slate-600">${f.pg}</td>
        <td class="py-2.5 px-2 text-center text-slate-600">${f.pe}</td><td class="py-2.5 px-2 text-center text-slate-600">${f.pp}</td>
        <td class="py-2.5 px-2 text-center text-slate-600">${f.gf}</td><td class="py-2.5 px-2 text-center text-slate-600">${f.gc}</td>
        <td class="py-2.5 px-2 text-center text-slate-600 tabular-nums">${f.dg > 0 ? "+" + f.dg : f.dg}</td>
        <td class="py-2.5 px-3 text-center font-bold text-blue-900">${f.pts}</td>
      </tr>`; }).join("")}
    </tbody>
  </table></div>`;
}

function tablaGoleadoresHTML(goleadores) {
  return `
  <div class="overflow-x-auto"><table class="w-full text-xs">
    <thead><tr class="text-slate-400 border-b border-slate-100">
      <th class="py-2.5 px-3 text-center font-medium">POS</th><th class="py-2.5 px-3 text-left font-medium">JUGADOR</th>
      <th class="py-2.5 px-3 text-left font-medium">INSTITUCIÓN</th><th class="py-2.5 px-2 text-center font-medium">CAMISETA</th>
      <th class="py-2.5 px-3 text-center font-medium">GOLES</th>
    </tr></thead>
    <tbody>
      ${goleadores.length === 0 ? `<tr><td colspan="5" class="py-8 text-center text-slate-400">Aún no se han registrado goles.</td></tr>` : ""}
      ${goleadores.map((g, idx) => { const j = getJugador(g.jugadorId), c = getColegio(g.colegioId); return `
      <tr class="border-b border-slate-50 last:border-0">
        <td class="py-2.5 px-3 text-center text-slate-500 font-semibold">${idx + 1}</td>
        <td class="py-2.5 px-3 font-medium text-slate-700">${esc(j?.nombre)}</td>
        <td class="py-2.5 px-3 text-slate-500">${esc(c?.nombre)}</td>
        <td class="py-2.5 px-2 text-center text-slate-500">#${j?.camiseta}</td>
        <td class="py-2.5 px-3 text-center font-extrabold text-emerald-700">${g.goles}</td>
      </tr>`; }).join("")}
    </tbody>
  </table></div>`;
}

/* ============================================================
   8. PANTALLA 2 — PLANILLA DIGITAL DEL ÁRBITRO
   ============================================================ */
function renderArbitro() {
  const disponibles = state.data.partidos.filter((p) => p.estado === "EN_VIVO" || p.estado === "PROGRAMADO");
  const a = state.arbitro;
  const partido = state.data.partidos.find((p) => p.id === a.selectedPartidoId);

  if (!partido) return `<div class="min-h-screen bg-slate-50 flex items-center justify-center px-6 text-center"><p class="text-sm text-slate-400">No hay partidos EN_VIVO ni PROGRAMADOS para arbitrar.</p></div>`;

  const local = getColegio(partido.local.colegioId), visitante = getColegio(partido.visitante.colegioId);
  const minutoActual = Math.floor(a.seconds / 60);
  const finalizado = partido.estado === "FINALIZADO";
  const eventosOrdenados = [...partido.eventos].reverse();

  return `
  <div class="min-h-screen bg-slate-50 pb-8">
    <div class="max-w-md mx-auto">
      <div class="px-4 pt-4">
        ${filterDropdown(null, a.selectedPartidoId, disponibles.map((p) => p.id), (id) => { const p = state.data.partidos.find((x) => x.id === id); return getColegio(p.local.colegioId)?.sigla + " vs " + getColegio(p.visitante.colegioId)?.sigla + " · " + p.hora; }, "select-partido")}
      </div>

      <div class="mx-4 mt-3 rounded-xl bg-blue-950 text-white p-4">
        <div class="flex items-center justify-between mb-3">
          <span class="inline-flex items-center gap-2 text-[11px] font-bold px-3 py-1 rounded-full ${finalizado ? "bg-slate-600" : "bg-red-600"}">
            ${!finalizado ? `<span class="relative flex h-2 w-2"><span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-white/80 opacity-75"></span><span class="relative inline-flex rounded-full h-2 w-2 bg-white"></span></span>` : ""}
            ${finalizado ? "FINALIZADO" : "EN VIVO · " + esc(partido.tiempo)}
          </span>
          ${!finalizado ? `<button data-action="toggle-tiempo" class="text-[11px] text-blue-200/70 underline underline-offset-2">cambiar tiempo</button>` : ""}
        </div>
        <div class="flex items-center justify-between gap-3">
          <div class="flex-1 text-center"><div class="text-xs font-semibold leading-tight">${esc(local?.nombre)}</div></div>
          <div class="text-3xl font-extrabold tabular-nums px-2">${partido.local.marcador ?? 0}&nbsp;–&nbsp;${partido.visitante.marcador ?? 0}</div>
          <div class="flex-1 text-center"><div class="text-xs font-semibold leading-tight">${esc(visitante?.nombre)}</div></div>
        </div>
        <div class="flex items-center justify-center gap-3 mt-4">
          <div class="font-mono text-xl font-bold tabular-nums bg-white/10 px-4 py-1.5 rounded-lg">${String(minutoActual).padStart(2, "0")}:${String(a.seconds % 60).padStart(2, "0")}</div>
          ${!finalizado ? `<button data-action="toggle-timer" class="flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold px-4 py-2 rounded-lg"><i data-lucide="${a.running ? "pause" : "play"}" class="w-3.5 h-3.5"></i>${a.running ? "Pausar" : "Iniciar"}</button>` : ""}
        </div>
      </div>

      <div class="grid grid-cols-2 gap-3 px-4 mt-4">
        ${equipoAcciones(local, finalizado, "local")}
        ${equipoAcciones(visitante, finalizado, "visitante")}
      </div>

      <div class="px-4 mt-6">
        <h3 class="text-xs font-semibold text-blue-950 mb-2 uppercase tracking-wide">Línea de tiempo</h3>
        <div class="flex flex-col gap-2">
          ${eventosOrdenados.length === 0 ? `<p class="text-xs text-slate-400 text-center py-6">Sin eventos registrados todavía.</p>` : ""}
          ${eventosOrdenados.map((ev) => { const meta = EVENT_META[ev.tipo]; const j = getJugador(ev.jugadorId), c = getColegio(ev.colegioId); return `
          <div class="flex items-center gap-3 rounded-lg border border-slate-100 px-3 py-2.5 ${meta.bg}">
            <span class="font-mono text-xs font-bold text-slate-500 w-8 shrink-0">${ev.minuto}'</span>
            <span class="text-base shrink-0">${meta.icon}</span>
            <div class="flex-1 min-w-0"><p class="text-xs font-semibold text-slate-700 truncate">#${j?.camiseta} ${esc(j?.nombre)}</p><p class="text-[11px] text-slate-500 truncate">${meta.label} · ${esc(c?.nombre)}</p></div>
            ${!finalizado ? `<button data-action="eliminar-evento" data-evento-id="${ev.id}" class="p-1.5 rounded-md text-slate-400 hover:text-red-600 hover:bg-white shrink-0" title="Eliminar evento"><i data-lucide="trash-2" class="w-3.5 h-3.5"></i></button>` : ""}
          </div>`; }).join("")}
        </div>
      </div>

      <div class="px-4 mt-6">
        ${finalizado
          ? `<div class="text-center text-xs font-semibold text-slate-500 bg-slate-100 rounded-xl py-3">Planilla confirmada — marcador final ${partido.local.marcador} – ${partido.visitante.marcador}</div>`
          : `<button data-action="finalizar-partido" class="w-full bg-blue-950 hover:bg-blue-900 text-white text-sm font-bold py-4 rounded-xl">Finalizar partido y confirmar planilla</button>`}
      </div>
    </div>

    ${a.modal ? selectorJugadorModal(a.modal) : ""}
  </div>`;
}

function equipoAcciones(colegio, disabled, equipo) {
  return `
  <div class="bg-white rounded-xl shadow-sm p-3">
    <p class="text-[11px] font-bold text-slate-500 text-center mb-2 truncate">${esc(colegio?.sigla)}</p>
    <div class="flex flex-col gap-2">
      <button ${disabled ? "disabled" : ""} data-action="abrir-modal" data-tipo="GOL" data-equipo="${equipo}" class="flex items-center justify-center gap-1.5 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-40 text-white text-xs font-bold py-3 rounded-lg"><i data-lucide="circle-dot" class="w-3.5 h-3.5"></i> + GOL</button>
      <button ${disabled ? "disabled" : ""} data-action="abrir-modal" data-tipo="TARJETA_AMARILLA" data-equipo="${equipo}" class="flex items-center justify-center gap-1.5 bg-amber-400 hover:bg-amber-500 disabled:opacity-40 text-blue-950 text-xs font-bold py-3 rounded-lg">🟨 AMARILLA</button>
      <button ${disabled ? "disabled" : ""} data-action="abrir-modal" data-tipo="TARJETA_ROJA" data-equipo="${equipo}" class="flex items-center justify-center gap-1.5 bg-red-600 hover:bg-red-700 disabled:opacity-40 text-white text-xs font-bold py-3 rounded-lg">🟥 ROJA</button>
    </div>
  </div>`;
}

function selectorJugadorModal(modal) {
  const partido = state.data.partidos.find((p) => p.id === state.arbitro.selectedPartidoId);
  const colegioId = modal.equipo === "local" ? partido.local.colegioId : partido.visitante.colegioId;
  const colegio = getColegio(colegioId);
  const meta = EVENT_META[modal.tipo];
  const jugadoresColegio = state.data.jugadores.filter((j) => j.colegioId === colegioId);
  const numeros = Array.from({ length: 20 }, (_, i) => i + 1);
  return `
  <div class="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/50 px-0 sm:px-4">
    <div class="bg-white w-full sm:max-w-md rounded-t-2xl sm:rounded-2xl p-4 max-h-[82vh] overflow-y-auto">
      <div class="flex items-center justify-between mb-1">
        <div class="flex items-center gap-2"><span class="text-lg">${meta.icon}</span><div><p class="text-sm font-bold text-blue-950">${meta.label}</p><p class="text-[11px] text-slate-500">${esc(colegio?.nombre)}</p></div></div>
        <button data-action="cerrar-modal" class="p-1.5 rounded-md text-slate-400 hover:bg-slate-100"><i data-lucide="x" class="w-4 h-4"></i></button>
      </div>
      <p class="text-[11px] text-slate-400 mt-3 mb-2 uppercase tracking-wide font-semibold">Selecciona el número de camiseta</p>
      <div class="grid grid-cols-4 gap-2">
        ${numeros.map((n) => { const j = jugadoresColegio.find((x) => x.camiseta === n); return `
        <button ${j ? `data-action="registrar-evento" data-jugador-id="${j.id}"` : "disabled"} class="flex flex-col items-center justify-center rounded-lg py-2.5 text-center border ${j ? "border-blue-950 bg-blue-950 text-white hover:bg-blue-900 cursor-pointer" : "border-slate-100 bg-slate-50 text-slate-300 cursor-not-allowed"}">
          <span class="text-sm font-extrabold">${n}</span>${j ? `<span class="text-[8.5px] leading-tight mt-0.5 px-0.5 truncate w-full">${esc(j.nombre.split(" ")[0])}</span>` : ""}
        </button>`; }).join("")}
      </div>
    </div>
  </div>`;
}

/* ============================================================
   9. PANTALLA 3 — PANEL DEL ENTRENADOR
   ============================================================ */
function renderCoach() {
  const c = state.coach;
  const colegio = getColegio(c.selectedColegioId);
  const jugadoresColegio = state.data.jugadores.filter((j) => j.colegioId === c.selectedColegioId);

  return `
  <div class="min-h-screen bg-slate-50 pb-16">
    <div class="mx-auto max-w-4xl px-4 pt-6">
      ${filterDropdown(null, c.selectedColegioId, state.data.colegios.map((x) => x.id), (id) => getColegio(id)?.nombre, "select-colegio")}

      <div class="bg-white rounded-xl shadow-sm p-5 mt-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div class="flex items-center gap-3">
          <div class="w-12 h-12 rounded-lg bg-blue-950 text-white flex items-center justify-center font-bold text-sm shrink-0">${esc(colegio?.sigla)}</div>
          <div><p class="text-sm font-bold text-blue-950">${esc(colegio?.nombre)}</p><p class="text-xs text-slate-500 mt-0.5">${jugadoresColegio.length} / ${CUPO_MAXIMO} convocados</p></div>
        </div>
        <div class="flex items-center gap-3">
          ${colegio?.estadoInscripcion === "VALIDADO"
            ? `<span class="inline-flex items-center gap-1.5 bg-emerald-50 text-emerald-700 text-xs font-bold px-3 py-1.5 rounded-full"><i data-lucide="check-circle-2" class="w-3.5 h-3.5"></i> Validado / Pago confirmado</span>`
            : `<span class="inline-flex items-center gap-1.5 bg-amber-50 text-amber-700 text-xs font-bold px-3 py-1.5 rounded-full"><i data-lucide="alert-circle" class="w-3.5 h-3.5"></i> Pendiente de pago</span>
               <button data-action="abrir-pago-modal" class="flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold px-4 py-2 rounded-lg"><i data-lucide="credit-card" class="w-3.5 h-3.5"></i> Pagar cuota de inscripción</button>`}
        </div>
      </div>

      ${formularioInscripcionHTML()}

      <div class="bg-white rounded-xl shadow-sm overflow-hidden mt-6">
        <div class="px-5 py-4 border-b border-slate-100"><h3 class="text-sm font-bold text-blue-950">Plantilla / nómina de jugadores</h3></div>
        <div class="overflow-x-auto"><table class="w-full text-xs">
          <thead><tr class="text-slate-400 border-b border-slate-100">
            <th class="py-2.5 px-4 text-center font-medium">#</th><th class="py-2.5 px-3 text-left font-medium">JUGADOR</th>
            <th class="py-2.5 px-3 text-center font-medium">POSICIÓN</th><th class="py-2.5 px-3 text-center font-medium">PAZ Y SALVO / DOCS</th>
            <th class="py-2.5 px-4 text-center font-medium">ACCIONES</th>
          </tr></thead>
          <tbody>
            ${jugadoresColegio.length === 0 ? `<tr><td colspan="5" class="py-8 text-center text-slate-400">Aún no hay jugadores inscritos para este colegio.</td></tr>` : ""}
            ${jugadoresColegio.map((j) => filaJugadorHTML(j)).join("")}
          </tbody>
        </table></div>
      </div>
    </div>

    ${c.showPagoModal ? pagoModalHTML(colegio) : ""}
  </div>`;
}

function filaJugadorHTML(j) {
  const enEdicion = state.coach.editingId === j.id;
  const draft = state.coach.editDraft;
  return `
  <tr class="border-b border-slate-50 last:border-0">
    <td class="py-2.5 px-4 text-center">
      ${enEdicion
        ? `<input type="number" data-role="edit-camiseta" value="${draft.camiseta}" class="w-14 border border-slate-200 rounded-md px-1.5 py-1 text-center">`
        : `<span class="inline-flex items-center justify-center w-7 h-7 rounded-full bg-blue-950 text-white font-bold text-[11px]">${j.camiseta}</span>`}
    </td>
    <td class="py-2.5 px-3"><p class="font-medium text-slate-700">${esc(j.nombre)}</p><p class="text-[11px] text-slate-400">${esc(j.documento)}</p></td>
    <td class="py-2.5 px-3 text-center">
      ${enEdicion
        ? `<select data-role="edit-posicion" class="border border-slate-200 rounded-md px-1.5 py-1 text-[11px]">${POSICIONES.map((p) => `<option value="${p}" ${p === draft.posicion ? "selected" : ""}>${p}</option>`).join("")}</select>`
        : `<span class="px-2.5 py-1 rounded-full text-[10.5px] font-semibold ${POSICION_COLOR[j.posicion]}">${j.posicion}</span>`}
    </td>
    <td class="py-2.5 px-3 text-center">
      ${j.pazYSalvo
        ? `<span class="inline-flex items-center gap-1 text-emerald-600 text-[11px] font-semibold"><i data-lucide="check-circle-2" class="w-3.5 h-3.5"></i> Verificado</span>`
        : `<button data-action="marcar-pazysalvo" data-jugador-id="${j.id}" class="inline-flex items-center gap-1 text-amber-600 text-[11px] font-semibold underline underline-offset-2"><i data-lucide="alert-circle" class="w-3.5 h-3.5"></i> Pendiente · cargar</button>`}
    </td>
    <td class="py-2.5 px-4"><div class="flex items-center justify-center gap-1.5">
      ${enEdicion
        ? `<button data-action="guardar-edicion" data-jugador-id="${j.id}" class="text-[11px] font-semibold text-emerald-700 px-2 py-1 rounded-md hover:bg-emerald-50">Guardar</button>
           <button data-action="cancelar-edicion" class="text-[11px] font-semibold text-slate-400 px-2 py-1 rounded-md hover:bg-slate-50">Cancelar</button>`
        : `<button data-action="iniciar-edicion" data-jugador-id="${j.id}" class="p-1.5 rounded-md text-slate-400 hover:text-blue-900 hover:bg-slate-50" title="Editar"><i data-lucide="pencil" class="w-3.5 h-3.5"></i></button>
           <button data-action="eliminar-jugador" data-jugador-id="${j.id}" class="p-1.5 rounded-md text-slate-400 hover:text-red-600 hover:bg-slate-50" title="Eliminar"><i data-lucide="trash-2" class="w-3.5 h-3.5"></i></button>`}
    </div></td>
  </tr>`;
}

let coachArchivoNombre = "";
function formularioInscripcionHTML() {
  return `
  <form id="form-inscripcion" class="bg-white rounded-xl shadow-sm p-5 mt-6">
    <h3 class="text-sm font-bold text-blue-950 mb-4">Inscribir jugador</h3>
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
      <div><label class="text-[11px] font-semibold text-slate-500 mb-1 block">Nombre completo</label><input id="input-nombre" placeholder="Ej. Camilo Reyes" class="w-full border border-slate-200 rounded-lg px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-emerald-600"></div>
      <div><label class="text-[11px] font-semibold text-slate-500 mb-1 block">Documento de identidad (TI/CC)</label><input id="input-documento" placeholder="Ej. 1098234099" class="w-full border border-slate-200 rounded-lg px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-emerald-600"></div>
      <div><label class="text-[11px] font-semibold text-slate-500 mb-1 block">Número de camiseta (1-99)</label><input id="input-camiseta" type="number" min="1" max="99" placeholder="Ej. 10" class="w-full border border-slate-200 rounded-lg px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-emerald-600"></div>
      <div><label class="text-[11px] font-semibold text-slate-500 mb-1 block">Posición</label><select id="select-posicion" class="w-full border border-slate-200 rounded-lg px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-emerald-600">${POSICIONES.map((p) => `<option value="${p}">${p}</option>`).join("")}</select></div>
    </div>
    <div class="mt-3">
      <label class="text-[11px] font-semibold text-slate-500 mb-1 block">Documento de identidad &amp; paz y salvo (.PDF / .JPG)</label>
      <div data-dropzone class="border-2 border-dashed border-slate-200 rounded-lg py-5 text-center cursor-pointer hover:border-emerald-500 hover:bg-emerald-50/30">
        <i data-lucide="upload-cloud" class="w-5 h-5 mx-auto text-slate-400 mb-1.5"></i>
        <p class="text-[11px] text-slate-500">${coachArchivoNombre ? `<span class="font-semibold text-emerald-700">${esc(coachArchivoNombre)}</span>` : "Arrastra el archivo aquí o haz clic para subirlo"}</p>
        <input data-role="coach-file-input" type="file" accept=".pdf,.jpg,.jpeg" class="hidden">
      </div>
    </div>
    <button type="submit" class="mt-4 w-full sm:w-auto flex items-center justify-center gap-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold px-5 py-2.5 rounded-lg">+ Inscribir jugador</button>
  </form>`;
}

function pagoModalHTML(colegio) {
  return `
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4">
    <div class="bg-white rounded-2xl p-5 max-w-sm w-full">
      <p class="text-sm font-bold text-blue-950 mb-1">Confirmar pago de inscripción</p>
      <p class="text-xs text-slate-500 mb-4">Se simulará el cobro de la cuota de inscripción para <b>${esc(colegio?.nombre)}</b>. Al confirmar, el estado del colegio pasará a "Validado".</p>
      <div class="flex justify-end gap-2">
        <button data-action="cerrar-pago-modal" class="text-xs font-semibold text-slate-500 px-3 py-2 rounded-lg hover:bg-slate-50">Cancelar</button>
        <button data-action="confirmar-pago" class="text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-700 px-4 py-2 rounded-lg">Confirmar pago</button>
      </div>
    </div>
  </div>`;
}

/* ============================================================
   10. PANTALLA 4 — PANEL DEL ADMINISTRADOR
   ============================================================ */
function renderAdmin() {
  const s = state.admin;
  return `
  <div class="min-h-screen bg-slate-50">
    <div class="flex flex-col md:flex-row">
      <aside class="w-full md:w-60 shrink-0 bg-blue-950 md:min-h-[calc(100vh-60px)] px-3 py-4">
        <div class="flex md:flex-col gap-1 overflow-x-auto">
          ${ADMIN_SECTIONS.map((sec) => `<button data-action="admin-section" data-section="${sec.id}" class="text-left whitespace-nowrap px-3 py-2.5 rounded-lg text-xs font-semibold transition-colors ${s.section === sec.id ? "bg-white text-blue-950" : "text-blue-200/75 hover:bg-white/10 hover:text-white"}">${sec.label}</button>`).join("")}
        </div>
      </aside>
      <main class="flex-1 px-4 sm:px-6 py-6 min-w-0">
        <div class="flex items-center justify-between flex-wrap gap-2 mb-6">
          <h2 class="text-lg font-bold text-blue-950">${ADMIN_SECTIONS.find((x) => x.id === s.section)?.label}</h2>
          <span class="inline-flex items-center gap-1.5 bg-blue-50 text-blue-900 text-[11px] font-bold px-3 py-1.5 rounded-full"><i data-lucide="shield-check" class="w-3.5 h-3.5"></i> Administrador del Sistema (RBAC · Acceso Total)</span>
        </div>
        ${s.section === "TORNEOS" ? seccionTorneosHTML() : ""}
        ${s.section === "FIXTURES" ? seccionFixturesHTML() : ""}
        ${s.section === "SEDES" ? seccionSedesHTML() : ""}
        ${s.section === "INSTITUCIONES" ? seccionInstitucionesHTML() : ""}
      </main>
    </div>
  </div>`;
}

function seccionTorneosHTML() {
  return `
  <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
    ${state.data.torneos.map((t) => `
    <div class="bg-white rounded-xl shadow-sm p-5">
      <p class="text-sm font-bold text-blue-950">${esc(t.nombre)}</p><p class="text-xs text-slate-500 mt-0.5">Categoría ${t.categoria}</p>
      <div class="mt-3"><label class="text-[11px] font-semibold text-slate-500 mb-1 block">Fase actual</label>
        <select data-action="cambiar-fase" data-torneo-id="${t.id}" class="w-full border border-slate-200 rounded-lg px-3 py-2 text-xs">
          <option ${t.fase === "Fase de Grupos" ? "selected" : ""}>Fase de Grupos</option>
          <option ${t.fase === "Eliminación Directa" ? "selected" : ""}>Eliminación Directa</option>
        </select>
      </div>
    </div>`).join("")}
  </div>`;
}

function seccionFixturesHTML() {
  const s = state.admin;
  const conflictos = {};
  state.data.partidos.forEach((p) => { const key = p.sedeId + "|" + p.fecha + "|" + p.hora; conflictos[key] = (conflictos[key] || 0) + 1; });
  const tieneConflicto = (p) => (conflictos[p.sedeId + "|" + p.fecha + "|" + p.hora] || 0) > 1;
  const partidosOrdenados = [...state.data.partidos].sort((a, b) => (a.fecha + a.hora).localeCompare(b.fecha + b.hora));

  return `
  <div class="flex flex-col gap-6">
    <div class="bg-white rounded-xl shadow-sm p-5">
      <h3 class="text-sm font-bold text-blue-950 mb-4">Configuración del fixture</h3>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
        <div><label class="text-[11px] font-semibold text-slate-500 mb-1 block">Categoría</label>
          <select data-bind="admin.categoria" class="w-full border border-slate-200 rounded-lg px-3 py-2 text-xs">
            <option ${s.categoria === "Sub-15" ? "selected" : ""}>Sub-15</option><option ${s.categoria === "Sub-17" ? "selected" : ""}>Sub-17</option>
          </select></div>
        <div><label class="text-[11px] font-semibold text-slate-500 mb-1 block">Sistema de competición</label>
          <select data-bind="admin.sistema" class="w-full border border-slate-200 rounded-lg px-3 py-2 text-xs">
            <option ${s.sistema === "Fase de Grupos" ? "selected" : ""}>Fase de Grupos</option><option ${s.sistema === "Eliminación Directa" ? "selected" : ""}>Eliminación Directa</option>
          </select></div>
      </div>
      <button data-action="generar-fixture" class="w-full sm:w-auto flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold px-5 py-3 rounded-lg">⚡ Generar fixture automático</button>
      <p class="text-[11px] text-slate-400 mt-2">Cruza únicamente colegios con inscripción <b>VALIDADO</b> y evita duplicar enfrentamientos ya existentes.</p>
    </div>

    <div class="bg-white rounded-xl shadow-sm overflow-hidden">
      <div class="px-5 py-4 border-b border-slate-100"><h3 class="text-sm font-bold text-blue-950">Partidos generados</h3></div>
      <div class="overflow-x-auto"><table class="w-full text-xs">
        <thead><tr class="text-slate-400 border-b border-slate-100">
          <th class="py-2.5 px-4 text-left font-medium">FECHA / HORA</th><th class="py-2.5 px-3 text-left font-medium">PARTIDO</th>
          <th class="py-2.5 px-3 text-left font-medium">SEDE / CANCHA</th><th class="py-2.5 px-3 text-left font-medium">ESTADO</th>
        </tr></thead>
        <tbody>
          ${partidosOrdenados.map((p) => { const conflicto = tieneConflicto(p); return `
          <tr class="border-b border-slate-50 last:border-0 align-top">
            <td class="py-2.5 px-4"><div class="flex flex-col gap-1">
              <input type="date" data-action="actualizar-partido" data-id="${p.id}" data-campo="fecha" value="${p.fecha}" class="border border-slate-200 rounded-md px-2 py-1 text-[11px]">
              <input type="time" data-action="actualizar-partido" data-id="${p.id}" data-campo="hora" value="${p.hora}" class="border border-slate-200 rounded-md px-2 py-1 text-[11px]">
            </div></td>
            <td class="py-2.5 px-3 font-medium text-slate-700">${esc(getColegio(p.local.colegioId)?.sigla)} <span class="text-slate-400 font-normal">vs</span> ${esc(getColegio(p.visitante.colegioId)?.sigla)}</td>
            <td class="py-2.5 px-3">
              <select data-action="actualizar-partido" data-id="${p.id}" data-campo="sedeId" class="border border-slate-200 rounded-md px-2 py-1.5 text-[11px] w-full">
                ${state.data.sedes.map((sd) => `<option value="${sd.id}" ${sd.id === p.sedeId ? "selected" : ""}>${esc(sd.nombre)}</option>`).join("")}
              </select>
              ${conflicto ? `<span class="mt-1.5 inline-flex items-center gap-1 bg-red-50 text-red-600 text-[10.5px] font-bold px-2 py-1 rounded-md">⚠️ Conflicto de Sede/Horario</span>` : ""}
            </td>
            <td class="py-2.5 px-3">
              <select data-action="actualizar-partido" data-id="${p.id}" data-campo="estado" class="border border-slate-200 rounded-md px-2 py-1.5 text-[11px]">
                ${ESTADOS_PARTIDO.map((es) => `<option value="${es}" ${es === p.estado ? "selected" : ""}>${es}</option>`).join("")}
              </select>
            </td>
          </tr>`; }).join("")}
        </tbody>
      </table></div>
    </div>
  </div>`;
}

let sedeForm = { nombre: "", direccion: "", tipoSuperficie: SUPERFICIES[0] };
function seccionSedesHTML() {
  return `
  <div class="flex flex-col gap-6">
    <form id="form-sede" class="bg-white rounded-xl shadow-sm p-5">
      <h3 class="text-sm font-bold text-blue-950 mb-4">Registrar nueva sede / cancha</h3>
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div><label class="text-[11px] font-semibold text-slate-500 mb-1 block">Nombre de la sede</label><input id="sede-nombre" placeholder="Ej. Cancha 4 — Villa Olímpica" class="w-full border border-slate-200 rounded-lg px-3 py-2 text-xs"></div>
        <div><label class="text-[11px] font-semibold text-slate-500 mb-1 block">Dirección</label><input id="sede-direccion" placeholder="Ej. Cra 20 #5-40" class="w-full border border-slate-200 rounded-lg px-3 py-2 text-xs"></div>
        <div><label class="text-[11px] font-semibold text-slate-500 mb-1 block">Tipo de superficie</label><select id="sede-superficie" class="w-full border border-slate-200 rounded-lg px-3 py-2 text-xs">${SUPERFICIES.map((sf) => `<option value="${sf}">${sf}</option>`).join("")}</select></div>
      </div>
      <button type="submit" class="mt-4 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold px-5 py-2.5 rounded-lg">+ Registrar sede</button>
    </form>
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
      ${state.data.sedes.map((s) => { const n = state.data.partidos.filter((p) => p.sedeId === s.id).length; return `
      <div class="bg-white rounded-xl shadow-sm p-4">
        <p class="text-sm font-bold text-blue-950">${esc(s.nombre)}</p><p class="text-[11px] text-slate-500 mt-0.5">${esc(s.direccion)}</p><p class="text-[11px] text-slate-500">Superficie: ${esc(s.tipoSuperficie)}</p>
        <span class="inline-flex items-center gap-1 mt-3 bg-blue-50 text-blue-900 text-[11px] font-bold px-2.5 py-1 rounded-full">${n} partido${n !== 1 ? "s" : ""} programado${n !== 1 ? "s" : ""}</span>
      </div>`; }).join("")}
    </div>
  </div>`;
}

function seccionInstitucionesHTML() {
  return `
  <div class="bg-white rounded-xl shadow-sm overflow-hidden"><div class="overflow-x-auto"><table class="w-full text-xs">
    <thead><tr class="text-slate-400 border-b border-slate-100">
      <th class="py-2.5 px-4 text-left font-medium">COLEGIO</th><th class="py-2.5 px-3 text-center font-medium">JUGADORES</th>
      <th class="py-2.5 px-3 text-center font-medium">ESTADO INSCRIPCIÓN</th><th class="py-2.5 px-4 text-center font-medium">ACCIONES</th>
    </tr></thead>
    <tbody>
      ${state.data.colegios.map((c) => { const total = state.data.jugadores.filter((j) => j.colegioId === c.id).length; return `
      <tr class="border-b border-slate-50 last:border-0">
        <td class="py-2.5 px-4 font-medium text-slate-700">${esc(c.nombre)}</td>
        <td class="py-2.5 px-3 text-center text-slate-600">${total}</td>
        <td class="py-2.5 px-3 text-center"><span class="px-2.5 py-1 rounded-full text-[10.5px] font-bold ${c.estadoInscripcion === "VALIDADO" ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"}">${c.estadoInscripcion}</span></td>
        <td class="py-2.5 px-4 text-center"><button data-action="toggle-estado-colegio" data-id="${c.id}" class="text-[11px] font-semibold text-blue-900 underline underline-offset-2">Alternar estado</button></td>
      </tr>`; }).join("")}
    </tbody>
  </table></div></div>`;
}

/* ============================================================
   11. ACCIONES (lógica de negocio)
   ============================================================ */
function handleAction(action, el) {
  const d = state.data;

  if (action === "dashboard-tab") { state.dashboard.tab = el.dataset.tab; render(); return; }

  if (action === "select-partido") {
    clearInterval(state.arbitro.timerId);
    state.arbitro.selectedPartidoId = el.value;
    const p = d.partidos.find((x) => x.id === el.value);
    state.arbitro.seconds = (p?.minutoActual || 0) * 60;
    state.arbitro.running = false;
    render();
    return;
  }
  if (action === "toggle-timer") {
    const p = d.partidos.find((x) => x.id === state.arbitro.selectedPartidoId);
    if (p.estado === "PROGRAMADO") p.estado = "EN_VIVO";
    state.arbitro.running = !state.arbitro.running;
    clearInterval(state.arbitro.timerId);
    if (state.arbitro.running) {
      state.arbitro.timerId = setInterval(() => { state.arbitro.seconds++; render(); }, 1000);
    }
    render();
    return;
  }
  if (action === "toggle-tiempo") {
    const p = d.partidos.find((x) => x.id === state.arbitro.selectedPartidoId);
    p.tiempo = p.tiempo === "Tiempo 1" ? "Tiempo 2" : "Tiempo 1";
    render();
    return;
  }
  if (action === "abrir-modal") { state.arbitro.modal = { tipo: el.dataset.tipo, equipo: el.dataset.equipo }; render(); return; }
  if (action === "cerrar-modal") { state.arbitro.modal = null; render(); return; }
  if (action === "registrar-evento") {
    const p = d.partidos.find((x) => x.id === state.arbitro.selectedPartidoId);
    const jugador = d.jugadores.find((j) => j.id === el.dataset.jugadorId);
    const modal = state.arbitro.modal;
    const minuto = Math.floor(state.arbitro.seconds / 60);
    p.eventos.push({ id: "e" + Date.now(), minuto, tipo: modal.tipo, jugadorId: jugador.id, colegioId: jugador.colegioId });
    if (modal.tipo === "GOL") p[modal.equipo].marcador = (p[modal.equipo].marcador || 0) + 1;
    state.arbitro.modal = null;
    render();
    return;
  }
  if (action === "eliminar-evento") {
    const p = d.partidos.find((x) => x.id === state.arbitro.selectedPartidoId);
    const ev = p.eventos.find((e) => e.id === el.dataset.eventoId);
    const equipo = ev.colegioId === p.local.colegioId ? "local" : "visitante";
    p.eventos = p.eventos.filter((e) => e.id !== ev.id);
    if (ev.tipo === "GOL") p[equipo].marcador = Math.max(0, (p[equipo].marcador || 0) - 1);
    render();
    return;
  }
  if (action === "finalizar-partido") {
    clearInterval(state.arbitro.timerId);
    state.arbitro.running = false;
    const p = d.partidos.find((x) => x.id === state.arbitro.selectedPartidoId);
    p.estado = "FINALIZADO";
    p.minutoActual = Math.floor(state.arbitro.seconds / 60);
    render();
    return;
  }

  if (action === "select-colegio") { state.coach.selectedColegioId = el.value; render(); return; }
  if (action === "abrir-pago-modal") { state.coach.showPagoModal = true; render(); return; }
  if (action === "cerrar-pago-modal") { state.coach.showPagoModal = false; render(); return; }
  if (action === "confirmar-pago") {
    const c = d.colegios.find((x) => x.id === state.coach.selectedColegioId);
    c.estadoInscripcion = "VALIDADO";
    state.coach.showPagoModal = false;
    render();
    mostrarToast("Pago confirmado — inscripción del colegio validada.");
    return;
  }
  if (action === "marcar-pazysalvo") {
    const j = d.jugadores.find((x) => x.id === el.dataset.jugadorId);
    j.pazYSalvo = true;
    render();
    return;
  }
  if (action === "eliminar-jugador") {
    d.jugadores = d.jugadores.filter((j) => j.id !== el.dataset.jugadorId);
    render();
    mostrarToast("Jugador eliminado de la plantilla.", "info");
    return;
  }
  if (action === "iniciar-edicion") {
    const j = d.jugadores.find((x) => x.id === el.dataset.jugadorId);
    state.coach.editingId = j.id;
    state.coach.editDraft = { camiseta: String(j.camiseta), posicion: j.posicion };
    render();
    return;
  }
  if (action === "cancelar-edicion") { state.coach.editingId = null; render(); return; }
  if (action === "guardar-edicion") {
    const j = d.jugadores.find((x) => x.id === el.dataset.jugadorId);
    const camisetaInput = document.querySelector('[data-role="edit-camiseta"]');
    const posicionInput = document.querySelector('[data-role="edit-posicion"]');
    const nuevaCamiseta = Number(camisetaInput.value);
    const nuevaPosicion = posicionInput.value;
    const jugadoresColegio = d.jugadores.filter((x) => x.colegioId === j.colegioId);
    if (!nuevaCamiseta || nuevaCamiseta < 1 || nuevaCamiseta > 99) { mostrarToast("El número de camiseta debe estar entre 1 y 99.", "error"); return; }
    if (jugadoresColegio.some((x) => x.id !== j.id && x.camiseta === nuevaCamiseta)) { mostrarToast(`La camiseta #${nuevaCamiseta} ya está asignada en este colegio.`, "error"); return; }
    j.camiseta = nuevaCamiseta; j.posicion = nuevaPosicion;
    state.coach.editingId = null;
    render();
    mostrarToast("Jugador actualizado.");
    return;
  }

  if (action === "admin-section") { state.admin.section = el.dataset.section; render(); return; }
  if (action === "cambiar-fase") {
    const t = d.torneos.find((x) => x.id === el.dataset.torneoId);
    t.fase = el.value;
    render();
    mostrarToast("Fase del torneo actualizada.");
    return;
  }
  if (action === "generar-fixture") {
    const validados = d.colegios.filter((c) => c.estadoInscripcion === "VALIDADO");
    if (validados.length < 2) { mostrarToast("Se necesitan al menos 2 colegios con inscripción VALIDADO.", "error"); return; }
    const pares = [];
    for (let i = 0; i < validados.length; i++) for (let j = i + 1; j < validados.length; j++) pares.push([validados[i], validados[j]]);
    const existentes = new Set(d.partidos.map((p) => [p.local.colegioId, p.visitante.colegioId].sort().join("-")));
    const nuevosPares = pares.filter(([a, b]) => !existentes.has([a.id, b.id].sort().join("-")));
    if (nuevosPares.length === 0) { mostrarToast("Ya existen todos los cruces posibles entre los colegios validados.", "info"); return; }
    const sedeDefault = d.sedes[0]?.id;
    const horarios = ["08:00", "10:00", "14:00"];
    const base = new Date(); base.setDate(base.getDate() + 7);
    const nuevos = nuevosPares.map(([a, b], idx) => {
      const fecha = new Date(base); fecha.setDate(fecha.getDate() + Math.floor(idx / horarios.length));
      return { id: `p${Date.now()}_${idx}`, torneoId: state.admin.categoria === "Sub-15" ? "t1" : "t2",
        local: { colegioId: a.id, marcador: null }, visitante: { colegioId: b.id, marcador: null },
        fecha: fecha.toISOString().slice(0, 10), hora: horarios[idx % horarios.length],
        minutoActual: 0, tiempo: "Tiempo 1", sedeId: sedeDefault, estado: "PROGRAMADO", eventos: [] };
    });
    d.partidos = [...d.partidos, ...nuevos];
    render();
    mostrarToast(`${nuevos.length} partido(s) de ${state.admin.sistema} generado(s) para ${state.admin.categoria}.`);
    return;
  }
  if (action === "actualizar-partido") {
    const p = d.partidos.find((x) => x.id === el.dataset.id);
    p[el.dataset.campo] = el.value;
    render();
    return;
  }
  if (action === "toggle-estado-colegio") {
    const c = d.colegios.find((x) => x.id === el.dataset.id);
    c.estadoInscripcion = c.estadoInscripcion === "VALIDADO" ? "PENDIENTE" : "VALIDADO";
    render();
    mostrarToast("Estado de inscripción del colegio actualizado.");
    return;
  }
}

/* ============================================================
   12. DELEGACIÓN DE EVENTOS
   ============================================================ */
document.addEventListener("click", (e) => {
  const nav = e.target.closest("[data-nav]");
  if (nav) { setView(nav.dataset.nav); return; }
  const dz = e.target.closest("[data-dropzone]");
  if (dz && !e.target.closest("input")) { dz.querySelector('[data-role="coach-file-input"]')?.click(); return; }
  const actionEl = e.target.closest("[data-action]");
  if (actionEl && actionEl.tagName !== "SELECT") { handleAction(actionEl.dataset.action, actionEl); }
});

document.addEventListener("change", (e) => {
  const bindEl = e.target.closest("[data-bind]");
  if (bindEl) { setPath(state, bindEl.dataset.bind, bindEl.value); render(); return; }
  const actionEl = e.target.closest("[data-action]");
  if (actionEl) { handleAction(actionEl.dataset.action, actionEl); return; }
  if (e.target.dataset.role === "coach-file-input") {
    const f = e.target.files?.[0];
    if (f) { coachArchivoNombre = f.name; render(); }
  }
});

document.addEventListener("dragover", (e) => { if (e.target.closest("[data-dropzone]")) e.preventDefault(); });
document.addEventListener("drop", (e) => {
  const dz = e.target.closest("[data-dropzone]");
  if (dz) { e.preventDefault(); const f = e.dataTransfer.files?.[0]; if (f) { coachArchivoNombre = f.name; render(); } }
});

document.addEventListener("submit", (e) => {
  if (e.target.id === "form-inscripcion") {
    e.preventDefault();
    const nombre = document.getElementById("input-nombre").value.trim();
    const documento = document.getElementById("input-documento").value.trim();
    const camisetaNum = Number(document.getElementById("input-camiseta").value);
    const posicion = document.getElementById("select-posicion").value;
    const colegioId = state.coach.selectedColegioId;
    const jugadoresColegio = state.data.jugadores.filter((j) => j.colegioId === colegioId);

    if (!nombre || !documento) { mostrarToast("Nombre y documento son obligatorios.", "error"); return; }
    if (!camisetaNum || camisetaNum < 1 || camisetaNum > 99) { mostrarToast("El número de camiseta debe estar entre 1 y 99.", "error"); return; }
    if (jugadoresColegio.some((j) => j.camiseta === camisetaNum)) { mostrarToast(`La camiseta #${camisetaNum} ya está asignada en este colegio.`, "error"); return; }

    state.data.jugadores.push({ id: "j" + Date.now(), colegioId, nombre, documento, camiseta: camisetaNum, posicion, pazYSalvo: Boolean(coachArchivoNombre) });
    coachArchivoNombre = "";
    render();
    mostrarToast(`${nombre} fue inscrito correctamente.`);
    return;
  }
  if (e.target.id === "form-sede") {
    e.preventDefault();
    const nombre = document.getElementById("sede-nombre").value.trim();
    const direccion = document.getElementById("sede-direccion").value.trim();
    const tipoSuperficie = document.getElementById("sede-superficie").value;
    if (!nombre || !direccion) { mostrarToast("Nombre y dirección de la sede son obligatorios.", "error"); return; }
    state.data.sedes.push({ id: "s" + Date.now(), nombre, direccion, tipoSuperficie });
    render();
    mostrarToast("Sede registrada correctamente.");
    return;
  }
});

/* ============================================================
   13. INICIO
   ============================================================ */
render();