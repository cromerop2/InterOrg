/* Interfaz conectada a la API. Los datos del torneo siempre vienen del servidor. */
import { createApi } from './api.js';

const $ = selector => document.querySelector(selector);
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const state = {
  token: sessionStorage.getItem('copa.token') || '', user: null,
  tournaments: [], teams: [], colleges: [], staff: [], tournament: '', tab: 'fixture',
  fixture: [], groups: [], entries: [], progress: null, team: '', roster: {},
  admin: false, section: 'torneo', busy: false, loading: true, error: '', revision: 0,
};
const api = createApi({
  getToken: () => state.token,
  onExpired: () => { clearSession(); toast('Tu sesión venció. Inicia sesión de nuevo.', true); render(); },
});
const isAdmin = () => state.user?.rol === 'Administrador';
const current = () => state.tournaments.find(t => String(t.id) === state.tournament);
const enrolled = () => state.teams.filter(t => state.entries.some(i => i.equipo_id === t.id));
const teamName = id => state.teams.find(t => t.id === id)?.nombre || 'Equipo';
const badge = text => `<span class="badge">${esc(text)}</span>`;
const empty = (title, text = '') => `<div class="empty"><span class="empty-symbol">◈</span><h3>${esc(title)}</h3><p>${esc(text)}</p></div>`;
const input = (name, label, type = 'text', extra = '') => `<label>${label}<input name="${name}" type="${type}" ${extra} required></label>`;
const options = (rows, label = 'nombre') => rows.map(r => `<option value="${r.id}">${esc(r[label])}</option>`).join('');
const select = (name, label, rows, field = 'nombre') => `<label>${label}<select name="${name}" required><option value="">Selecciona…</option>${options(rows, field)}</select></label>`;
function form(kind, title, content, button) {
  return `<section class="panel"><h2>${title}</h2><form data-form="${kind}"><div class="form-grid">${content}</div><p class="form-error" role="alert"></p><button class="button primary" type="submit">${button}</button></form></section>`;
}
function toast(message, error = false) {
  $('#toast-root').innerHTML = `<div class="toast ${error ? 'error' : ''}" role="${error ? 'alert' : 'status'}">${esc(message)}</div>`;
  clearTimeout(toast.timer); toast.timer = setTimeout(() => $('#toast-root').replaceChildren(), 6500);
}
function clearSession() {
  state.token = ''; state.user = null; state.admin = false; state.staff = [];
  sessionStorage.removeItem('copa.token');
}
function render() {
  $('#header').innerHTML = `<header class="topbar"><div class="brand"><span class="brand-icon">◈</span><div>COPA <strong>COLEGIAL</strong><small>El campeonato, más cerca.</small></div></div>
    <nav aria-label="Navegación principal"><button data-action="public" class="${!state.admin ? 'active' : ''}">Campeonato</button>
    ${isAdmin() ? `<button data-action="admin" class="${state.admin ? 'active' : ''}">Administrar</button>` : ''}
    <button data-action="${state.user ? 'logout' : 'login'}" class="access">${state.user ? 'Cerrar sesión' : 'Acceso administrador'}</button></nav></header>`;
  const main = $('#main');
  if (state.loading && !state.tournaments.length) { main.innerHTML = '<main class="container"><div class="loading" role="status">Conectando con el campeonato…</div></main>'; return; }
  main.innerHTML = `<main class="container">${state.error ? `<div class="error-box" role="alert">${esc(state.error)} <button data-action="refresh">Reintentar</button></div>` : ''}
    ${state.admin && isAdmin() ? renderAdmin() : renderPublic()}</main><footer>TORNEO COLEGIAL <span>Grupos · Eliminatorias · Una misma pasión</span></footer>`;
  main.querySelectorAll('button[type="submit"]').forEach(button => { button.disabled = state.busy; });
}
function renderPublic() {
  const t = current(), p = state.progress;
  return `<section class="hero"><div class="hero-copy"><span class="eyebrow"><span class="dot"></span> EL DEPORTE NOS UNE</span>
    <h1>${esc(t?.nombre || 'Cada equipo tiene una historia.')}</h1><p>${t ? esc(t.categoria) + ' · Grupos y eliminatorias' : 'Sigue a tu equipo y vive cada etapa del campeonato.'}</p>
    ${t ? badge(t.estado.replaceAll('_', ' ')) : ''}</div><div class="pitch" aria-hidden="true"><div></div><span>◈</span></div></section>
    <section class="toolbar"><div><span class="eyebrow dark">EXPLORA EL CAMPEONATO</span><h2>Todo lo que está pasando</h2></div>
      <div class="toolbar-controls"><label class="sr-only" for="tournament">Campeonato</label><select id="tournament" ${state.loading ? 'disabled' : ''}>
      <option value="">Selecciona un campeonato</option>${state.tournaments.map(t => `<option value="${t.id}" ${String(t.id) === state.tournament ? 'selected' : ''}>${esc(t.nombre)} · ${esc(t.categoria)}</option>`).join('')}</select>
      <button class="button secondary" data-action="refresh" ${state.loading ? 'disabled' : ''}>↻ Actualizar</button></div></section>
    ${!t ? empty('Aún no hay un campeonato seleccionado', 'El administrador puede crear uno y registrar a los equipos.') : `
      <div class="stats"><article><span>EQUIPOS INSCRITOS</span><strong>${p?.equipos_inscritos ?? '—'}</strong></article><article><span>PARTIDOS FINALIZADOS</span><strong>${p?.partidos_finalizados ?? '—'}</strong></article><article><span>PRÓXIMOS PARTIDOS</span><strong>${p?.partidos_pendientes ?? '—'}</strong></article><article class="phase-stat"><span>FASE ACTUAL</span><strong>${esc(p?.fase_actual || 'Inscripciones')}</strong></article></div>
      ${p?.campeon ? `<div class="champion"><span>★</span><div><small>CAMPEÓN DEL TORNEO</small><h2>${esc(p.campeon)}</h2></div></div>` : ''}
      <div class="content-layout"><section class="panel results"><div class="tabs" role="tablist">${[['fixture','Fixture'],['posiciones','Posiciones'],['equipos','Equipos']].map(([id,label]) => `<button role="tab" aria-selected="${state.tab === id}" data-tab="${id}" class="${state.tab === id ? 'selected' : ''}">${label}</button>`).join('')}</div>
        <div class="tab-body" role="tabpanel">${state.tab === 'fixture' ? renderFixture() : state.tab === 'posiciones' ? renderPositions() : renderTeams()}</div></section>
      <aside class="panel follow"><span class="eyebrow dark">EL CAMINO AL TÍTULO</span><h2>Un paso a la vez</h2><ol><li class="done">Inscripción de equipos</li><li class="${state.fixture.length ? 'done' : ''}">Fase de grupos</li><li class="${state.fixture.some(p => p.tipo_fase === 'Eliminatoria_Directa') ? 'done' : ''}">Eliminatorias</li><li class="${p?.campeon ? 'done' : ''}">La gran final</li></ol><p>Las posiciones y resultados se actualizan con los marcadores oficiales.</p><p class="last-update">${state.loading ? 'Actualizando…' : 'Datos del servidor · Actualización cada 30 s'}</p></aside></div>`}`;
}
function renderFixture() {
  const matches = state.fixture.filter(p => !state.team || p.equipo_local_id === Number(state.team) || p.equipo_visitante_id === Number(state.team));
  return `<div class="section-heading"><div><h2>El calendario del torneo</h2><p>Encuentra los encuentros de tu equipo.</p></div><label>Tu equipo<select id="team-filter"><option value="">Todos los equipos</option>${enrolled().map(t => `<option value="${t.id}" ${String(t.id) === state.team ? 'selected' : ''}>${esc(t.nombre)}</option>`).join('')}</select></label></div>
    ${!matches.length ? empty('Todavía no hay partidos', state.fixture.length ? 'Prueba con otro equipo.' : 'El fixture aparecerá cuando el administrador lo genere.') : matches.map(p => `<article class="match"><div class="match-top"><span>${esc(p.fase)}${p.grupo ? ' · ' + esc(p.grupo) : ''} · Jornada ${p.jornada}</span>${badge(p.estado)}</div><div class="scoreline"><strong>${esc(p.equipo_local)}</strong><div>${p.estado === 'Finalizado' ? `${p.goles_local}<span>–</span>${p.goles_visitante}` : '<span>VS</span>'}</div><strong>${esc(p.equipo_visitante)}</strong></div>
    ${p.penales_local !== null ? `<p class="penalties">Penales ${p.penales_local} – ${p.penales_visitante}</p>` : ''}<div class="match-bottom"><span>${p.fecha_hora ? esc(new Date(p.fecha_hora).toLocaleString('es-CO', { dateStyle:'medium', timeStyle:'short' })) : 'Fecha por confirmar'}</span><span>${esc(p.sede || 'Sede por confirmar')}</span></div></article>`).join('')}`;
}
function renderPositions() {
  return state.groups.length ? state.groups.map(g => `<section class="group"><h2>${esc(g.nombre)}</h2><div class="table-wrap"><table><thead><tr><th>POS</th><th>EQUIPO</th>${['PJ','PG','PE','PP','GF','GC','DG','PTS'].map(x => `<th>${x}</th>`).join('')}</tr></thead><tbody>${g.posiciones.map(f => `<tr><td>${f.posicion}</td><th scope="row">${esc(f.equipo)}</th>${['pj','pg','pe','pp','gf','gc','dg','puntos'].map(x => `<td>${f[x]}</td>`).join('')}</tr>`).join('')}</tbody></table></div><p class="table-note">${esc(g.criterio_desempate)}</p></section>`).join('') : empty('Las posiciones están por comenzar', 'La tabla se creará junto con los grupos.');
}
function renderTeams() {
  return enrolled().length ? `<div class="team-grid">${enrolled().map(t => `<article class="team-card"><div class="team-avatar">${esc(t.nombre.slice(0,2).toUpperCase())}</div><h3>${esc(t.nombre)}</h3><p>${esc(state.colleges.find(c => c.id === t.colegio_id)?.nombre || 'Institución participante')}</p><button class="button secondary" data-roster="${t.id}">Ver plantilla</button>
    ${state.roster[t.id] ? `<ul class="roster">${state.roster[t.id].length ? state.roster[t.id].map(j => `<li><span>#${j.numero_camiseta ?? '—'}</span>${esc(j.nombre_completo)}</li>`).join('') : '<li>Aún no hay jugadores registrados.</li>'}</ul>` : ''}</article>`).join('')}</div>` : empty('Los equipos están por llegar', 'Aquí aparecerán los equipos inscritos en este campeonato.');
}
function renderAdmin() {
  const t = current();
  const tabs = [['torneo','Campeonatos'],['equipos','Equipos y jugadores'],['instituciones','Instituciones y staff'],['partidos','Fixture y resultados']];
  let body = '';
  if (state.section === 'torneo') {
    body = form('tournament', 'Crear campeonato',
      input('nombre','Nombre') + input('categoria','Categoría') + input('fecha_inicio','Fecha de inicio','date') + input('fecha_fin','Fecha de fin','date') +
      input('numero_grupos','Número de grupos','number','min="1" max="32" value="2"') + input('clasifican_por_grupo','Clasificados por grupo','number','min="1" max="8" value="2"'), 'Crear campeonato') +
      `<section class="panel"><h2>Inscribir equipos</h2><p>Selecciona un campeonato en la lista superior. El total de clasificados debe ser 2, 4, 8, 16…</p>
      ${t ? `<h3>${esc(t.nombre)} · ${esc(t.estado)}</h3><form data-form="enroll"><div class="form-grid">${select('equipo_id','Equipo', state.teams.filter(e => !state.entries.some(i => i.equipo_id === e.id)))}</div><p class="form-error" role="alert"></p><button class="button primary" ${t.estado !== 'Inscripciones' ? 'disabled' : ''}>Inscribir equipo</button></form><ul class="enroll-list">${state.entries.map(i => `<li>${esc(teamName(i.equipo_id))}${t.estado === 'Inscripciones' ? `<button type="button" class="text-danger" data-remove-team="${i.equipo_id}">Retirar</button>` : ''}</li>`).join('')}</ul>` : empty('Selecciona o crea un campeonato') }</section>`;
  } else if (state.section === 'equipos') {
    body = form('team','Crear equipo',input('nombre','Nombre del equipo') + select('colegio_id','Colegio',state.colleges) + select('entrenador_id','Entrenador',state.staff.filter(u => u.rol === 'Entrenador'), 'nombre_completo'), 'Crear equipo') +
      form('player','Registrar jugador',select('equipo_id','Equipo',state.teams) + input('nombre_completo','Nombre completo') + input('identificacion','Documento') + input('fecha_nacimiento','Fecha de nacimiento','date') + '<label>Número de camiseta<input name="numero_camiseta" type="number" min="0"></label>', 'Registrar jugador');
  } else if (state.section === 'instituciones') {
    body = form('college','Crear colegio',input('nombre','Nombre del colegio') + input('direccion','Dirección') + input('representante_legal','Representante legal') + input('telefono_contacto','Teléfono','tel') + '<label>Correo institucional<input name="email_institucional" type="email"></label>', 'Crear colegio') +
      form('staff','Crear entrenador',input('nombre_completo','Nombre completo') + input('email','Correo','email') + input('telefono_contacto','Teléfono','tel') + input('password','Contraseña inicial','password','minlength="8" autocomplete="new-password"'), 'Crear entrenador');
  } else {
    body = `<section class="panel"><h2>Fixture y rondas</h2><p>Genera los grupos cuando termines las inscripciones. Avanza de fase después de registrar todos sus resultados.</p><div class="actions"><button class="button primary" data-action="generate" ${!t || t.estado !== 'Inscripciones' || state.busy ? 'disabled' : ''}>Generar grupos y fixture</button><button class="button secondary" data-action="advance" ${!t || t.estado !== 'En_Curso' || state.busy ? 'disabled' : ''}>Generar siguiente ronda</button></div></section>` +
      (state.fixture.length ? state.fixture.map(p => `<section class="panel"><div class="section-heading"><h2>${esc(p.equipo_local)} vs ${esc(p.equipo_visitante)}</h2>${badge(p.fase)}</div>
      <form data-form="schedule" data-id="${p.id}"><div class="form-grid">${input('fecha_hora','Fecha y hora local','datetime-local')} ${input('sede','Sede')}</div><p class="form-error" role="alert"></p><button class="button secondary" ${p.estado === 'Finalizado' ? 'disabled' : ''}>Guardar programación</button></form>
      <form data-form="result" data-id="${p.id}"><h3>Resultado oficial</h3><div class="form-grid">${input('goles_local','Goles local','number',`min="0" max="999" value="${p.goles_local ?? ''}"`)}${input('goles_visitante','Goles visitante','number',`min="0" max="999" value="${p.goles_visitante ?? ''}"`)}
      ${p.tipo_fase !== 'Grupos' ? `<label>Penales local (solo empate)<input name="penales_local" type="number" min="0" value="${p.penales_local ?? ''}"></label><label>Penales visitante<input name="penales_visitante" type="number" min="0" value="${p.penales_visitante ?? ''}"></label>` : ''}</div><p class="form-error" role="alert"></p><button class="button primary">Guardar resultado</button></form></section>`).join('') : empty('Aún no hay partidos', 'Primero crea un campeonato e inscribe sus equipos.'));
  }
  return `<div class="admin-heading"><span class="eyebrow dark">ADMINISTRACIÓN</span><h1>Organiza el campeonato</h1><p>Sesión de ${esc(state.user.nombre_completo)} · Los cambios se guardan en el servidor.</p></div>
    <label class="tournament-admin">Campeonato activo<select id="tournament"><option value="">Selecciona…</option>${state.tournaments.map(t => `<option value="${t.id}" ${String(t.id) === state.tournament ? 'selected' : ''}>${esc(t.nombre)}</option>`).join('')}</select></label>
    <div class="admin-layout"><nav class="admin-nav" aria-label="Secciones de administración">${tabs.map(([id,label]) => `<button data-section="${id}" class="${state.section === id ? 'selected' : ''}">${label}</button>`).join('')}</nav><div class="admin-content">${body}</div></div>`;
}
async function load({ background = false } = {}) {
  if (state.busy || (background && state.admin)) return;
  const revision = ++state.revision;
  if (!background) { state.loading = true; render(); }
  try {
    const [tournaments, teams, colleges] = await Promise.all([api('/torneos/'), api('/equipos/'), api('/colegios/')]);
    if (revision !== state.revision) return;
    state.tournaments = tournaments; state.teams = teams; state.colleges = colleges;
    if (!tournaments.some(t => String(t.id) === state.tournament)) state.tournament = tournaments.length ? String(tournaments[0].id) : '';
    if (state.tournament) {
      const id = state.tournament;
      const [fixture, groups, progress, entries] = await Promise.all(['fixture','posiciones','seguimiento','equipos'].map(path => api(`/torneos/${id}/${path}`)));
      if (revision !== state.revision || id !== state.tournament) return;
      Object.assign(state, { fixture, groups, progress, entries });
    } else Object.assign(state, { fixture: [], groups: [], entries: [], progress: null });
    if (isAdmin() && !background) state.staff = await api('/usuarios/?limit=100');
    state.error = '';
  } catch (error) { if (revision === state.revision) state.error = error.message; }
  finally { if (revision === state.revision) { state.loading = false; render(); } }
}
function showLogin() {
  const dialog = $('#login-dialog');
  dialog.innerHTML = `<button class="close" aria-label="Cerrar" type="button">×</button><span class="eyebrow dark">BIENVENIDO DE NUEVO</span><h2 id="login-title">Acceso administrador</h2><p>Entra con la cuenta creada para el torneo.</p><form data-form="login"><div class="form-grid single">${input('email','Correo','email','autocomplete="username"')}${input('password','Contraseña','password','autocomplete="current-password"')}</div><p class="form-error" role="alert"></p><button class="button primary">Entrar</button></form>`;
  dialog.querySelector('.close').onclick = () => dialog.close();
  dialog.showModal();
}
async function mutate(path, method, body) {
  if (state.busy) return;
  state.busy = true;
  try { return await api(path, {method, body}); }
  finally { state.busy = false; }
}
document.addEventListener('submit', async event => {
  const form = event.target.closest('form[data-form]'); if (!form) return;
  event.preventDefault(); if (state.busy) return;
  const data = Object.fromEntries(new FormData(form));
  const errorBox = form.querySelector('.form-error'); errorBox.textContent = '';
  const button = form.querySelector('button[type="submit"], button:not([type])');
  if (button) button.disabled = true;
  try {
    const kind = form.dataset.form;
    const numeric = keys => keys.forEach(key => { if (data[key] !== undefined) data[key] = data[key] === '' ? null : Number(data[key]); });
    if (kind === 'login') {
      const result = await mutate('/auth/login','POST',data);
      state.token = result.access_token; sessionStorage.setItem('copa.token',state.token);
      state.user = await api('/auth/me'); state.admin = isAdmin();
      $('#login-dialog').close();
      toast(isAdmin() ? 'Sesión iniciada.' : 'Sesión iniciada. Tu rol puede consultar el campeonato.');
    } else if (kind === 'tournament') {
      numeric(['numero_grupos','clasifican_por_grupo']);
      const result = await mutate('/torneos/','POST',data); state.tournament = String(result.id); toast('Campeonato creado.');
    } else if (kind === 'team') {
      numeric(['colegio_id','entrenador_id']); await mutate('/equipos/','POST',data); toast('Equipo creado.');
    } else if (kind === 'player') {
      numeric(['equipo_id','numero_camiseta']); await mutate('/jugadores/','POST',data); state.roster = {}; toast('Jugador registrado.');
    } else if (kind === 'college') {
      if (!data.email_institucional) delete data.email_institucional;
      await mutate('/colegios/','POST',data); toast('Colegio creado.');
    } else if (kind === 'staff') {
      await mutate('/usuarios/','POST',{...data,rol:'Entrenador'}); toast('Entrenador creado.');
    } else if (kind === 'enroll') {
      numeric(['equipo_id']); await mutate(`/torneos/${state.tournament}/equipos`,'POST',data); toast('Equipo inscrito.');
    } else if (kind === 'schedule') {
      data.fecha_hora = new Date(data.fecha_hora).toISOString();
      await mutate(`/partidos/${form.dataset.id}/programacion`,'PATCH',data); toast('Programación guardada.');
    } else if (kind === 'result') {
      numeric(['goles_local','goles_visitante','penales_local','penales_visitante']);
      await mutate(`/partidos/${form.dataset.id}/resultado`,'PUT',data); toast('Resultado guardado.');
    }
    await load();
  } catch (error) { errorBox.textContent = error.message; }
  finally { if (button?.isConnected) button.disabled = false; }
});
document.addEventListener('change', async event => {
  if (event.target.id === 'tournament') { state.tournament = event.target.value; state.team = ''; await load(); }
  if (event.target.id === 'team-filter') { state.team = event.target.value; render(); }
});
document.addEventListener('click', async event => {
  const target = event.target.closest('button'); if (!target || target.disabled) return;
  if (target.dataset.tab) { state.tab = target.dataset.tab; render(); return; }
  if (target.dataset.section) { state.section = target.dataset.section; render(); return; }
  try {
    if (target.dataset.roster) { state.roster[target.dataset.roster] = await api(`/equipos/${target.dataset.roster}/jugadores`); render(); }
    if (target.dataset.removeTeam && confirm('¿Retirar este equipo del campeonato?')) {
      await mutate(`/torneos/${state.tournament}/equipos/${target.dataset.removeTeam}`,'DELETE'); await load(); toast('Equipo retirado.');
    }
    switch (target.dataset.action) {
      case 'login': showLogin(); break;
      case 'logout': await api('/auth/logout',{method:'POST'}); clearSession(); render(); break;
      case 'public': state.admin = false; await load(); break;
      case 'admin': state.admin = true; await load(); break;
      case 'refresh': await load(); break;
      case 'generate': case 'advance':
        if (state.busy) break;
        if (!confirm(target.dataset.action === 'generate' ? '¿Generar los grupos y cerrar las inscripciones?' : '¿Generar la siguiente ronda? Los resultados de la fase anterior quedarán cerrados.')) break;
        await mutate(`/torneos/${state.tournament}/${target.dataset.action === 'generate' ? 'fixture' : 'avanzar'}`,'POST');
        await load(); toast('Fixture actualizado.'); break;
    }
  } catch (error) { toast(error.message, true); }
});
async function init() {
  if (state.token) {
    try { state.user = await api('/auth/me'); }
    catch (error) { if (error.status === 401) clearSession(); else toast(error.message,true); }
  }
  await load();
}
setInterval(() => { if (!document.hidden && !$('#login-dialog').open) load({background:true}); }, 30000);
document.addEventListener('visibilitychange', () => { if (!document.hidden && !state.admin) load({background:true}); });
init();
