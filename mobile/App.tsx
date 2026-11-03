/** Aplicación nativa: el servidor es la única fuente de fixtures y posiciones. */
import React, { useCallback, useEffect, useRef, useState } from 'react';
import { ActivityIndicator, AppState, KeyboardAvoidingView, Platform, RefreshControl, ScrollView, Text, View } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import { ApiError, AsyncStorage, normalizeUrl, request, tokenStore, URL_KEY } from './src/api';
import { Button, Choice, Field, Option, colors, s } from './src/ui';
import type { College, Entry, Group, Match, Player, Progress, Team, Tournament, User } from './src/types';

type Tab = 'fixture'|'posiciones'|'equipos'|'cuenta';
type Action = { kind:string; title:string; match?:Match };
type FieldSpec = { name:string; label:string; type?:'number'|'password'; options?:Option[]; optional?:boolean; placeholder?:string };
const rows = (items:{id:number;nombre?:string;nombre_completo?:string}[]):Option[] => items.map(i=>({id:String(i.id),label:i.nombre || i.nombre_completo || String(i.id)}));
const emptyData = { tournaments:[] as Tournament[],teams:[] as Team[],colleges:[] as College[],staff:[] as User[],matches:[] as Match[],groups:[] as Group[],entries:[] as Entry[],progress:null as Progress|null };
const dateText = (date:string|null) => date ? new Date(date).toLocaleString('es-CO',{dateStyle:'medium',timeStyle:'short'}) : 'Fecha por confirmar';

function DataForm({fields,title,busy,onSubmit,onCancel}:{fields:FieldSpec[];title:string;busy:boolean;onSubmit:(data:Record<string,string>)=>Promise<void>;onCancel:()=>void}) {
  const [values,setValues] = useState<Record<string,string>>({});
  const [error,setError] = useState('');
  async function submit() {
    const missing = fields.find(f=>!f.optional && !values[f.name]?.trim());
    if (missing) { setError('Completa el campo: ' + missing.label); return; }
    setError('');
    try { await onSubmit(values); } catch (e) { setError(e instanceof Error ? e.message : 'No se pudo guardar.'); }
  }
  return <View style={s.card}><Text style={s.title}>{title}</Text>{fields.map(f=>f.options
    ? <Choice key={f.name} label={f.label} value={values[f.name] || ''} options={f.options} onChange={v=>setValues(p=>({...p,[f.name]:v}))}/>
    : <Field key={f.name} label={f.label} value={values[f.name] || ''} onChange={v=>setValues(p=>({...p,[f.name]:v}))} secure={f.type==='password'} numeric={f.type==='number'} placeholder={f.placeholder} autoCapitalize={['email','fecha_hora','fecha_inicio','fecha_fin','fecha_nacimiento'].includes(f.name)?'none':'sentences'}/>)}
    {!!error&&<Text accessibilityRole="alert" style={s.error}>{error}</Text>}
    <Button title={busy?'Guardando…':'Guardar'} disabled={busy} onPress={submit}/><Button title="Volver" secondary disabled={busy} onPress={onCancel}/>
  </View>;
}
function MatchCard({match,admin,onAction}:{match:Match;admin:boolean;onAction:(a:Action)=>void}) {
  return <View style={s.card}><View style={s.between}><Text style={[s.text,{flex:1}]}>{match.fase}{match.grupo?' · '+match.grupo:''} · J{match.jornada}</Text><Text style={s.badge}>{match.estado}</Text></View>
    <View style={s.row}><Text style={s.team}>{match.equipo_local}</Text><Text style={s.score}>{match.estado==='Finalizado' ? match.goles_local+' – '+match.goles_visitante : 'vs'}</Text><Text style={s.team}>{match.equipo_visitante}</Text></View>
    {match.penales_local!==null&&<Text style={[s.text,{textAlign:'center'}]}>Penales {match.penales_local} – {match.penales_visitante}</Text>}
    <Text style={s.text}>{dateText(match.fecha_hora)}{'\n'}{match.sede || 'Sede por confirmar'}</Text>
    {admin&&<View style={s.row}><View style={{flex:1}}><Button title="Resultado" onPress={()=>onAction({kind:'result',title:'Resultado oficial',match})}/></View>{match.estado!=='Finalizado'&&<View style={{flex:1}}><Button title="Programar" secondary onPress={()=>onAction({kind:'schedule',title:'Programar partido',match})}/></View>}</View>}
  </View>;
}
function AppContent() {
  const [base,setBase] = useState('');
  const [urlInput,setUrlInput] = useState(process.env.EXPO_PUBLIC_API_URL || '');
  const [connection,setConnection] = useState(false);
  const [token,setToken] = useState('');
  const [user,setUser] = useState<User|null>(null);
  const [data,setData] = useState(emptyData);
  const [selected,setSelected] = useState('');
  const [team,setTeam] = useState('');
  const [tab,setTab] = useState<Tab>('fixture');
  const [loading,setLoading] = useState(true);
  const [busy,setBusy] = useState(false);
  const [error,setError] = useState('');
  const [notice,setNotice] = useState('');
  const [action,setAction] = useState<Action|null>(null);
  const [rosters,setRosters] = useState<Record<number,Player[]>>({});
  const revision = useRef(0);
  const alive = useRef(true);
  const mutating = useRef(false);
  const admin = user?.rol === 'Administrador';
  const current = data.tournaments.find(t=>String(t.id)===selected);
  const enrolled = data.teams.filter(t=>data.entries.some(i=>i.equipo_id===t.id));
  const clearLogin = useCallback(async()=>{
    await tokenStore.clear(); setToken(''); setUser(null); setAction(null); setData(p=>({...p,staff:[]}));
  },[]);
  const api = useCallback(async<T,>(path:string,method='GET',body?:unknown):Promise<T>=>{
    try { return await request<T>(base,path,token,method,body); }
    catch (e) {
      if (e instanceof ApiError && e.status===401 && token && path!=='/auth/login') {
        await clearLogin(); setNotice('Tu sesión venció. Inicia sesión de nuevo.');
      }
      throw e;
    }
  },[base,token,clearLogin]);
  const load = useCallback(async(background=false)=>{
    if (!base || mutating.current) return;
    const version = ++revision.current;
    if (!background) setLoading(true);
    try {
      const [tournaments,teams,colleges] = await Promise.all([api<Tournament[]>('/torneos/'),api<Team[]>('/equipos/'),api<College[]>('/colegios/')]);
      const id = tournaments.some(t=>String(t.id)===selected) ? selected : tournaments[0] ? String(tournaments[0].id) : '';
      const details = id ? await Promise.all([api<Match[]>(`/torneos/${id}/fixture`),api<Group[]>(`/torneos/${id}/posiciones`),api<Entry[]>(`/torneos/${id}/equipos`),api<Progress>(`/torneos/${id}/seguimiento`)]) : [[],[],[],null] as [Match[],Group[],Entry[],Progress|null];
      const staff = admin ? await api<User[]>('/usuarios/?limit=100') : [];
      if (alive.current && version===revision.current) {
        setData({tournaments,teams,colleges,staff,matches:details[0],groups:details[1],entries:details[2],progress:details[3]});
        setSelected(id); setError('');
      }
    } catch (e) { if (alive.current && version===revision.current) setError(e instanceof Error ? e.message : 'Error de conexión.'); }
    finally { if (alive.current && version===revision.current) setLoading(false); }
  },[api,base,selected,admin]);
  useEffect(()=>{
    alive.current = true;
    (async()=>{
      try {
        const saved = await AsyncStorage.getItem(URL_KEY);
        const savedToken = await tokenStore.get();
        if (!alive.current) return;
        if (saved) {
          setBase(saved); setUrlInput(saved);
          if (savedToken) {
            try { const profile = await request<User>(saved,'/auth/me',savedToken); if(alive.current){setToken(savedToken);setUser(profile);} }
            catch(e) { if(e instanceof ApiError && e.status===401) await tokenStore.clear(); else setNotice('No se pudo restaurar la sesión. Puedes iniciar sesión de nuevo.'); }
          }
        } else setConnection(true);
      } catch { if(alive.current)setConnection(true); }
      finally { if(alive.current)setLoading(false); }
    })();
    return ()=>{alive.current=false;revision.current++;};
  },[]);
  useEffect(()=>{ if(base)load(); },[load,base]);
  useEffect(()=>{
    if (!base) return;
    const timer=setInterval(()=>{if(AppState.currentState==='active'&&!action&&!connection)load(true);},30000);
    const subscription=AppState.addEventListener('change',next=>{if(next==='active'&&!action&&!connection)load(true);});
    return ()=>{clearInterval(timer);subscription.remove();};
  },[load,base,action,connection]);
  async function connect() {
    if(mutating.current)return;
    setBusy(true);setError('');
    try {
      const normalized=normalizeUrl(urlInput);
      await request<Tournament[]>(normalized,'/torneos/');
      if(normalized!==base) { await clearLogin(); setData(emptyData);setSelected('');setTeam('');setRosters({}); }
      await AsyncStorage.setItem(URL_KEY,normalized);
      setBase(normalized);setConnection(false);setNotice('Conexión lista.');
    } catch(e) {setError(e instanceof Error ? e.message : 'Dirección inválida.');}
    finally{setBusy(false);}
  }
  async function mutate<T>(path:string,method='POST',body?:unknown):Promise<T> {
    if(mutating.current)throw new Error('Hay otra operación en curso.');
    mutating.current=true;setBusy(true);
    try{return await api<T>(path,method,body);}
    finally{mutating.current=false;setBusy(false);}
  }
  const go = (a:Action)=>{setAction(a);setNotice('');setTab('cuenta');};
  function fieldsFor(a:Action):FieldSpec[] {
    const f=(name:string,label:string,extra:Partial<FieldSpec>={}):FieldSpec=>({name,label,...extra});
    switch(a.kind){
      case 'login':return[f('email','Correo'),f('password','Contraseña',{type:'password'})];
      case 'tournament':return[f('nombre','Nombre del campeonato'),f('categoria','Categoría'),f('fecha_inicio','Fecha de inicio',{placeholder:'2026-11-01'}),f('fecha_fin','Fecha de fin',{placeholder:'2026-12-31'}),f('numero_grupos','Número de grupos',{type:'number'}),f('clasifican_por_grupo','Clasificados por grupo',{type:'number'})];
      case 'college':return[f('nombre','Nombre del colegio'),f('direccion','Dirección'),f('representante_legal','Representante legal'),f('telefono_contacto','Teléfono')];
      case 'staff':return[f('nombre_completo','Nombre del entrenador'),f('email','Correo'),f('telefono_contacto','Teléfono'),f('password','Contraseña inicial',{type:'password'})];
      case 'team':return[f('nombre','Nombre del equipo'),f('colegio_id','Colegio',{options:rows(data.colleges)}),f('entrenador_id','Entrenador',{options:rows(data.staff.filter(u=>u.rol==='Entrenador'))})];
      case 'player':return[f('equipo_id','Equipo',{options:rows(data.teams)}),f('nombre_completo','Nombre completo'),f('identificacion','Documento'),f('fecha_nacimiento','Fecha de nacimiento',{placeholder:'2010-01-01'}),f('numero_camiseta','Número de camiseta',{optional:true,type:'number'})];
      case 'enroll':return[f('equipo_id','Equipo a inscribir',{options:rows(data.teams.filter(t=>!data.entries.some(i=>i.equipo_id===t.id)))})];
      case 'schedule':return[f('fecha_hora','Fecha y hora con zona',{placeholder:'2026-11-15T10:00:00-05:00'}),f('sede','Sede')];
      case 'result':return[f('goles_local','Goles local',{type:'number'}),f('goles_visitante','Goles visitante',{type:'number'}),...(a.match?.tipo_fase!=='Grupos'?[f('penales_local','Penales local (solo empate)',{optional:true,type:'number'}),f('penales_visitante','Penales visitante (solo empate)',{optional:true,type:'number'})]:[])];
      default:return[];
    }
  }
  async function submitForm(values:Record<string,string>) {
    if(!action)return;
    const d:Record<string,unknown>={...values};
    const number=(...keys:string[])=>keys.forEach(k=>{if(k in d)d[k]=d[k]===''?null:Number(d[k]);});
    if(action.kind==='login'){
      const session=await mutate<{access_token:string}>('/auth/login','POST',d);
      const profile=await request<User>(base,'/auth/me',session.access_token);
      await tokenStore.set(session.access_token);setToken(session.access_token);setUser(profile);
    } else if(action.kind==='tournament'){
      number('numero_grupos','clasifican_por_grupo');const t=await mutate<Tournament>('/torneos/','POST',d);setSelected(String(t.id));
    } else if(action.kind==='college')await mutate('/colegios/','POST',d);
    else if(action.kind==='staff')await mutate('/usuarios/','POST',{...d,rol:'Entrenador'});
    else if(action.kind==='team'){number('colegio_id','entrenador_id');await mutate('/equipos/','POST',d);}
    else if(action.kind==='player'){number('equipo_id','numero_camiseta');await mutate('/jugadores/','POST',d);setRosters({});}
    else if(action.kind==='enroll'){number('equipo_id');await mutate(`/torneos/${selected}/equipos`,'POST',d);}
    else if(action.kind==='schedule')await mutate(`/partidos/${action.match!.id}/programacion`,'PATCH',d);
    else if(action.kind==='result'){number('goles_local','goles_visitante','penales_local','penales_visitante');await mutate(`/partidos/${action.match!.id}/resultado`,'PUT',d);}
    setAction(null);setNotice(action.kind==='login'?'Sesión iniciada.':'Cambios guardados en el servidor.');
    await load();
  }
  async function operation(kind:'fixture'|'avanzar'){
    try {await mutate(`/torneos/${selected}/${kind}`);setNotice('Fixture actualizado.');await load();}
    catch(e){setError(e instanceof Error?e.message:'No se pudo guardar.');}
  }
  async function logout(){
    try{await api('/auth/logout','POST');await clearLogin();setNotice('Sesión cerrada.');}
    catch(e){if(e instanceof ApiError && e.status===401)await clearLogin();else setError('No se pudo cerrar la sesión en el servidor. Intenta de nuevo.');}
  }
  const filterMatches=data.matches.filter(p=>!team||p.equipo_local_id===Number(team)||p.equipo_visitante_id===Number(team));
  let body:React.ReactNode;
  if(connection){
    body=<View style={s.card}><Text style={s.title}>Conecta tu campeonato</Text><Text style={s.text}>Escribe la dirección del backend en tu computador. Ambos dispositivos deben estar en la misma red Wi-Fi.</Text><Field label="Dirección del backend" value={urlInput} onChange={setUrlInput} autoCapitalize="none" placeholder="http://192.168.1.54:8001"/><Text style={s.text}>En un teléfono físico, localhost no es tu computador. Usa su dirección IPv4.</Text><Button title={busy?'Conectando…':'Conectar'} disabled={busy} onPress={connect}/>{!!base&&<Button title="Cancelar" secondary onPress={()=>{setConnection(false);setError('');}}/>}</View>;
  } else if(action){
    body=<DataForm key={action.kind+String(action.match?.id||'')} title={action.title} fields={fieldsFor(action)} busy={busy} onSubmit={submitForm} onCancel={()=>setAction(null)}/>;
  } else if(tab==='cuenta'){
    body=<><View style={s.card}><Text style={s.title}>{user?user.nombre_completo:'Tu cuenta'}</Text><Text style={s.text}>{user?user.rol:'Los fixtures, resultados y posiciones son públicos. El administrador inicia sesión para organizar el campeonato.'}</Text>{user?<Button title="Cerrar sesión" secondary onPress={logout}/>:<Button title="Iniciar sesión" onPress={()=>go({kind:'login',title:'Acceso administrador'})}/>}</View>
      {admin&&<View style={s.card}><Text style={s.h2}>Administración</Text><Button title="Crear campeonato" onPress={()=>go({kind:'tournament',title:'Crear campeonato'})}/><Button title="Crear colegio" secondary onPress={()=>go({kind:'college',title:'Crear colegio'})}/><Button title="Crear entrenador" secondary onPress={()=>go({kind:'staff',title:'Crear entrenador'})}/><Button title="Crear equipo" secondary onPress={()=>go({kind:'team',title:'Crear equipo'})}/><Button title="Registrar jugador" secondary onPress={()=>go({kind:'player',title:'Registrar jugador'})}/>
      {!!current&&<><Text style={s.h2}>{current.nombre}</Text><Button title="Inscribir equipo" disabled={current.estado!=='Inscripciones'||busy} onPress={()=>go({kind:'enroll',title:'Inscribir equipo'})}/><Button title="Generar grupos y fixture" disabled={current.estado!=='Inscripciones'||busy} onPress={()=>operation('fixture')}/><Button title="Generar siguiente ronda" secondary disabled={current.estado!=='En_Curso'||busy} onPress={()=>operation('avanzar')}/><Text style={s.text}>Generar el fixture cierra las inscripciones. Avanzar de ronda bloquea los resultados de la fase anterior. Registra resultados desde la pestaña Fixture.</Text></>}</View>}
      <View style={s.card}><Text style={s.h2}>Conexión</Text><Text selectable style={s.text}>{base}</Text><Button title="Cambiar servidor" secondary onPress={()=>{setUrlInput(base);setConnection(true);setError('');}}/></View></>;
  } else if(!current){
    body=<View style={s.card}><Text style={s.title}>Cada equipo tiene una historia</Text><Text style={s.text}>Todavía no hay campeonatos. El administrador puede crear uno desde Cuenta.</Text></View>;
  } else if(tab==='fixture'){
    body=<><View style={s.hero}><Text style={s.eyebrow}>EL DEPORTE NOS UNE</Text><Text style={s.heroTitle}>{current.nombre}</Text><Text style={{color:'#c4d6e5'}}>{current.categoria} · {data.progress?.fase_actual||'Inscripciones'}</Text></View>
      {data.progress?.campeon&&<View style={s.notice}><Text style={[s.eyebrow,{color:colors.green}]}>CAMPEÓN DEL TORNEO</Text><Text style={s.title}>★ {data.progress.campeon}</Text></View>}
      <View style={s.row}>{[['Equipos',data.progress?.equipos_inscritos],['Finalizados',data.progress?.partidos_finalizados],['Pendientes',data.progress?.partidos_pendientes]].map(([label,value])=><View key={String(label)} style={s.stat}><Text style={s.statNumber}>{value??'—'}</Text><Text style={s.statLabel}>{label}</Text></View>)}</View>
      <Choice label="Tu equipo" value={team} options={[{id:'',label:'Todos los equipos'},...rows(enrolled)]} onChange={setTeam}/>
      {!filterMatches.length&&<View style={s.card}><Text style={s.h2}>Los encuentros están por comenzar</Text><Text style={s.text}>El fixture aparecerá cuando el administrador lo genere.</Text></View>}
      {filterMatches.map(match=><MatchCard key={match.id} match={match} admin={admin} onAction={go}/>)}</>;
  } else if(tab==='posiciones'){
    body=data.groups.length?data.groups.map(group=><View style={s.card} key={group.id}><Text style={s.h2}>{group.nombre}</Text><ScrollView horizontal><View><View style={[s.row,{paddingBottom:10}]}>{['POS','EQUIPO','PJ','PG','PE','PP','GF','GC','DG','PTS'].map((label,i)=><Text key={label} style={{width:i===1?145:34,fontSize:10,fontWeight:'700',color:colors.muted}}>{label}</Text>)}</View>{group.posiciones.map(row=><View key={row.equipo_id} style={[s.row,s.listItem]}>{[row.posicion,row.equipo,row.pj,row.pg,row.pe,row.pp,row.gf,row.gc,row.dg,row.puntos].map((value,i)=><Text key={i} style={{width:i===1?145:34,fontSize:12,color:i===9?colors.green:colors.navy,fontWeight:i===1||i===9?'700':'400'}}>{value}</Text>)}</View>)}</View></ScrollView><Text style={s.text}>{group.criterio_desempate}</Text></View>):<View style={s.card}><Text style={s.h2}>La tabla está por comenzar</Text><Text style={s.text}>Se publicará junto con los grupos del campeonato.</Text></View>;
  } else {
    body=enrolled.length?enrolled.map(t=><View key={t.id} style={s.card}><Text style={s.title}>{t.nombre}</Text><Text style={s.text}>{data.colleges.find(c=>c.id===t.colegio_id)?.nombre}</Text><Button title="Ver plantilla" secondary onPress={async()=>{try{const players=await api<Player[]>(`/equipos/${t.id}/jugadores`);setRosters(p=>({...p,[t.id]:players}));}catch(e){setError(e instanceof Error?e.message:'Error');}}}/>
      {rosters[t.id]?.map(j=><Text key={j.id} style={s.text}>#{j.numero_camiseta??'—'} · {j.nombre_completo}</Text>)}{rosters[t.id]?.length===0&&<Text style={s.text}>Todavía no hay jugadores registrados.</Text>}</View>):<View style={s.card}><Text style={s.h2}>Equipos por confirmar</Text><Text style={s.text}>Aquí verás los equipos inscritos.</Text></View>;
  }
  return <SafeAreaView style={s.screen}><StatusBar style="dark"/><View style={s.header}><View><Text style={s.brand}>◈ COPA COLEGIAL</Text><Text style={s.subtitle}>El campeonato, más cerca.</Text></View>{loading&&<ActivityIndicator color={colors.green}/>}</View>
    <KeyboardAvoidingView behavior={Platform.OS==='ios'?'padding':undefined} style={{flex:1}}><ScrollView keyboardShouldPersistTaps="handled" contentContainerStyle={s.content} refreshControl={<RefreshControl refreshing={loading && !!base && !connection} onRefresh={()=>load()} tintColor={colors.green}/>}>
      {!!error&&<View style={[s.card,{borderColor:'#e8c7cd'}]}><Text accessibilityRole="alert" style={s.error}>{error}</Text>{!connection&&<><Button title="Reintentar" secondary onPress={()=>load()}/><Button title="Revisar conexión" secondary onPress={()=>{setUrlInput(base);setConnection(true);setError('');}}/></>}</View>}
      {!!notice&&<View style={s.notice}><Text style={{color:'#146f54',fontSize:12}}>{notice}</Text></View>}
      {!connection&&!action&&data.tournaments.length>0&&<Choice label="Campeonato" value={selected} options={data.tournaments.map(t=>({id:String(t.id),label:t.nombre+' · '+t.categoria}))} onChange={v=>{setSelected(v);setTeam('');}}/>}
      {body}
    </ScrollView></KeyboardAvoidingView>
    {!connection&&<View style={s.tabs}>{([['fixture','◷','Fixture'],['posiciones','▤','Posiciones'],['equipos','♧','Equipos'],['cuenta','◉','Cuenta']] as const).map(([id,icon,label])=><View key={id} style={{flex:1}}><Button title={icon+' '+label} secondary={tab!==id} onPress={()=>{setTab(id);setAction(null);setError('');setNotice('');}}/></View>)}</View>}
  </SafeAreaView>;
}
export default function App(){return <SafeAreaProvider><AppContent/></SafeAreaProvider>;}
