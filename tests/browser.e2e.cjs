/* Pruebas reales de la web y de la versión web de la app nativa, con API temporal. */
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const os = require('node:os');
const http = require('node:http');
const net = require('node:net');
const {spawn} = require('node:child_process');
let playwright;
try { playwright = require('playwright'); }
catch { playwright = require(path.join(os.homedir(),'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright')); }
const root = path.resolve(__dirname,'..');
const screenshots = path.join(root,'test-results');
const delay = ms => new Promise(r=>setTimeout(r,ms));
async function freePort() {
  const server=net.createServer();await new Promise(r=>server.listen(0,'127.0.0.1',r));
  const port=server.address().port;await new Promise(r=>server.close(r));return port;
}
async function visible(locator) { await locator.waitFor({state:'visible',timeout:20000}); }
async function main(){
  await fs.mkdir(screenshots,{recursive:true});
  const temporary=await fs.mkdtemp(path.join(os.tmpdir(),'isi-ui-'));
  const stop=path.join(temporary,'stop');
  const port=await freePort();
  const base='http://127.0.0.1:'+port;
  const python=process.env.TEST_PYTHON || path.join(root,'backend/.venv/Scripts/python.exe');
  let output='',browser,staticServer;
  const processServer=spawn(python,[path.join(root,'tests/browser_server.py'),path.join(temporary,'test.sqlite3'),String(port),stop],{cwd:root,windowsHide:true});
  processServer.stdout.on('data',s=>output+=s);processServer.stderr.on('data',s=>output+=s);
  try{
    let ready=false;
    for(let n=0;n<100;n++){try{if((await fetch(base+'/openapi.json')).ok){ready=true;break;}}catch{} await delay(150);}
    assert.ok(ready,'El servidor no arrancó: '+output);
    browser=await playwright.chromium.launch({headless:true,channel:process.env.TEST_BROWSER_CHANNEL || 'chrome'});
    const page=await browser.newPage({viewport:{width:1440,height:1000}});
    const errors=[];page.on('pageerror',e=>errors.push(e.message));
    page.on('dialog',dialog=>dialog.accept());
    await page.goto(base);
    await visible(page.getByText('Aún no hay un campeonato seleccionado'));
    await page.getByRole('button',{name:'Acceso administrador',exact:true}).click();
    await page.getByLabel('Correo',{exact:true}).fill('admin@example.com');
    await page.getByLabel('Contraseña',{exact:true}).fill('incorrecta');
    await page.getByRole('button',{name:'Entrar',exact:true}).click();
    await visible(page.getByText('Credenciales inválidas.'));
    await page.getByLabel('Contraseña',{exact:true}).fill('PruebaNavegador123!');
    await page.getByRole('button',{name:'Entrar',exact:true}).click();
    await visible(page.getByRole('heading',{name:'Organiza el campeonato'}));
    async function fillForm(kind,values){
      const form=page.locator('form[data-form="'+kind+'"]');
      for(const [name,value] of Object.entries(values)){
        const input=form.locator('[name="'+name+'"]');
        if(await input.evaluate(el=>el.tagName)==='SELECT')await input.selectOption(String(value));
        else await input.fill(String(value));
      }
      await form.getByRole('button',{name:/Crear|Registrar|Guardar|Inscribir/}).click();
      await page.waitForFunction(()=>!document.querySelector('form button.primary:disabled'));
      await delay(150);
      assert.equal(await page.locator('.form-error').allTextContents().then(xs=>xs.join('').trim()),'');
    }
    await page.getByRole('button',{name:'Instituciones y staff'}).click();
    await fillForm('college',{nombre:'Colegio API',direccion:'Calle 10',representante_legal:'Ana Pérez',telefono_contacto:'3001234567'});
    await fillForm('staff',{nombre_completo:'Entrenador API',email:'coach@example.com',telefono_contacto:'3007654321',password:'Entrenador123!'});
    await page.getByRole('button',{name:'Equipos y jugadores'}).click();
    for(const nombre of ['Equipo A','Equipo B','Equipo C','Equipo D'])await fillForm('team',{nombre,colegio_id:'1',entrenador_id:'2'});
    await fillForm('player',{equipo_id:'1',nombre_completo:'Jugador API',identificacion:'DOC001',fecha_nacimiento:'2010-01-01',numero_camiseta:'10'});
    await page.getByRole('button',{name:'Campeonatos',exact:true}).click();
    await fillForm('tournament',{nombre:'Copa Integración',categoria:'Sub-17',fecha_inicio:'2026-11-01',fecha_fin:'2026-12-31',numero_grupos:'2',clasifican_por_grupo:'1'});
    await visible(page.getByRole('heading',{name:'Copa Integración · Inscripciones'}));
    for(let id=1;id<=4;id++)await fillForm('enroll',{equipo_id:String(id)});
    await page.getByRole('button',{name:'Fixture y resultados',exact:true}).click();
    await page.getByRole('button',{name:'Generar grupos y fixture'}).click();
    await page.locator('form[data-form="result"]').first().waitFor();
    assert.equal(await page.locator('form[data-form="result"]').count(),2);
    for(const id of ['1','2']){
      const form=page.locator('form[data-form="result"][data-id="'+id+'"]');
      await form.locator('[name="goles_local"]').fill('2');await form.locator('[name="goles_visitante"]').fill('1');
      await form.getByRole('button',{name:'Guardar resultado'}).click();
      await page.waitForFunction(()=>!document.querySelector('form button.primary:disabled'));
      await delay(100);
    }
    await page.getByRole('button',{name:'Generar siguiente ronda'}).click();
    const final=page.locator('form[data-form="result"][data-id="3"]');
    await visible(final);await final.locator('[name="goles_local"]').fill('1');await final.locator('[name="goles_visitante"]').fill('0');
    await final.getByRole('button',{name:'Guardar resultado'}).click();
    await page.waitForFunction(()=>!document.querySelector('form button.primary:disabled'));await delay(150);
    await page.getByRole('button',{name:'Campeonato',exact:true}).click();
    await visible(page.getByText('CAMPEÓN DEL TORNEO'));
    await page.screenshot({path:path.join(screenshots,'web-desktop.png'),fullPage:true});
    await page.getByRole('tab',{name:'Posiciones',exact:true}).click();
    assert.equal(await page.locator('section.group').count(),2);
    await page.getByRole('tab',{name:'Equipos',exact:true}).click();
    await page.getByRole('button',{name:'Ver plantilla'}).first().click();
    await visible(page.getByText('Jugador API'));
    await page.getByRole('button',{name:'Cerrar sesión',exact:true}).click();
    await page.reload();await visible(page.getByText('CAMPEÓN DEL TORNEO'));
    assert.equal(await page.getByRole('button',{name:'Administrar',exact:true}).count(),0);
    await page.setViewportSize({width:390,height:844});
    await page.getByRole('tab',{name:'Fixture',exact:true}).click();
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'La web tiene desbordamiento horizontal');
    await page.screenshot({path:path.join(screenshots,'web-phone.png'),fullPage:true});
    // La exportación web ejecuta los mismos componentes y transporte de la app nativa.
    staticServer=http.createServer(async(req,res)=>{
      try{
        const pathname=new URL(req.url,'http://localhost').pathname;
        const file=path.resolve(root,'mobile/dist','.'+decodeURIComponent(pathname==='/'?'/index.html':pathname));
        if(!file.startsWith(path.resolve(root,'mobile/dist')+path.sep)){res.writeHead(403);res.end();return;}
        const content=await fs.readFile(file);
        res.setHeader('Content-Type',file.endsWith('.js')?'application/javascript':file.endsWith('.html')?'text/html':file.endsWith('.png')?'image/png':'application/octet-stream');
        res.end(content);
      }catch{res.writeHead(404);res.end();}
    });
    await new Promise(r=>staticServer.listen(0,'127.0.0.1',r));
    const mobilePage=await browser.newPage({viewport:{width:390,height:844}});
    mobilePage.on('pageerror',e=>errors.push(e.message));
    await mobilePage.goto('http://127.0.0.1:'+staticServer.address().port);
    await mobilePage.getByLabel('Dirección del backend',{exact:true}).fill(base);
    await mobilePage.getByRole('button',{name:'Conectar',exact:true}).click();
    await visible(mobilePage.getByText('Copa Integración',{exact:true}));
    await visible(mobilePage.getByText(/★ Equipo/));
    await mobilePage.getByRole('button',{name:/▤ Posiciones/}).click();
    await visible(mobilePage.getByText('Grupo 1',{exact:true}));
    await mobilePage.getByRole('button',{name:/♧ Equipos/}).click();
    await mobilePage.getByRole('button',{name:'Ver plantilla',exact:true}).first().click();
    await visible(mobilePage.getByText('#10 · Jugador API',{exact:true}));
    await mobilePage.getByRole('button',{name:/◉ Cuenta/}).click();
    await mobilePage.getByRole('button',{name:'Iniciar sesión',exact:true}).click();
    await mobilePage.getByLabel('Correo',{exact:true}).fill('admin@example.com');
    await mobilePage.getByLabel('Contraseña',{exact:true}).fill('PruebaNavegador123!');
    await mobilePage.getByRole('button',{name:'Guardar',exact:true}).click();
    await visible(mobilePage.getByText('Administración',{exact:true}));
    await mobilePage.getByRole('button',{name:/◷ Fixture/}).click();
    await visible(mobilePage.getByRole('button',{name:'Resultado',exact:true}).first());
    await mobilePage.screenshot({path:path.join(screenshots,'mobile-app.png'),fullPage:true});
    await mobilePage.reload();
    await visible(mobilePage.getByText('Copa Integración',{exact:true}));
    assert.deepEqual(errors,[],'Errores JavaScript');
    console.log('OK: web + app, API real, administración, fixture, campeón, persistencia y consultas públicas.');
  }finally{
    if(browser)await browser.close();
    if(staticServer)await new Promise(r=>staticServer.close(r));
    await fs.writeFile(stop,'');
    if(processServer.exitCode===null)await Promise.race([new Promise(r=>processServer.once('exit',r)),delay(6000)]);
    if(processServer.exitCode===null)processServer.kill();
    // Elimina únicamente los archivos conocidos dentro del directorio temporal propio.
    if(path.dirname(temporary)===os.tmpdir()&&path.basename(temporary).startsWith('isi-ui-')){
      for(const name of ['stop','test.sqlite3','test.sqlite3-journal'])await fs.unlink(path.join(temporary,name)).catch(()=>{});
      await fs.rmdir(temporary).catch(()=>{});
    }
  }
}
main().catch(error=>{console.error(error);process.exitCode=1;});
