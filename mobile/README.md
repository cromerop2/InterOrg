# App móvil · Copa Colegial

Aplicación de React Native, TypeScript y Expo para Android e iOS. Incluye fixture
por equipo, posiciones por grupo, campeón y plantillas. El administrador puede
crear colegios, entrenadores, campeonatos, equipos y jugadores, inscribir equipos,
generar grupos/rondas y registrar programación y resultados.

Los datos se guardan en la misma API que utiliza la web. No se utilizan datos
simulados. El token se guarda con SecureStore en Android/iOS; en la vista web de
la app se utiliza sessionStorage. Cambiar de servidor elimina la sesión anterior.

## Probar en el teléfono

1. Instala **Expo Go** en Android o iPhone desde [Expo](https://expo.dev/go).
2. Conecta el teléfono y el computador a la misma red Wi-Fi.
3. Desde la raíz del repositorio abre una terminal PowerShell y arranca el backend:

   ```powershell
   powershell -ExecutionPolicy Bypass -File .\scripts\Start-Backend.ps1
   ```

   Este comando utiliza `backend/campeonato_prueba_manual.sqlite3`, la misma base
   de la prueba manual anterior. Crea únicamente las tablas que falten. Si tu base
   tiene otro nombre, pasa `-Database "otro_archivo.sqlite3"`. No modifica `.env`.
   Si ya hay otro servidor en el puerto 8001, detén el anterior con Ctrl+C.
4. En una **segunda terminal**, desde la raíz:

   ```powershell
   powershell -ExecutionPolicy Bypass -File .\scripts\Start-Mobile.ps1
   ```

   El script utiliza npm instalado o el runtime portátil disponible en este PC.
   En otro computador, instala primero Node.js LTS. Si faltan dependencias, las
   instala con `npm ci`. Después muestra el QR de Expo Go.
5. En Android escanea el QR desde Expo Go. En iPhone escanéalo con la Cámara y
   abre el enlace en Expo Go. Si iPhone solicita cuenta, inicia sesión con la
   misma cuenta de Expo en Expo Go y en el CLI. Detén Expo con Ctrl+C y repite
   el comando del paso 4 añadiendo `-Login`. También puedes usar `npx expo login`
   desde mobile si tienes Node.js instalado normalmente.
6. En la pantalla **Conecta tu campeonato**, comprueba la dirección del backend.
   Usa la IPv4 de la red del teléfono que muestra Start-Backend, por ejemplo:

   ```text
   http://192.168.1.54:8001
   ```

   Pulsa **Conectar**. En un teléfono físico, `localhost` y `127.0.0.1` apuntan al
   teléfono, no al PC. Puedes cambiar la dirección desde **Cuenta → Cambiar servidor**.
7. Consulta Fixture, Posiciones y Equipos. En **Cuenta → Iniciar sesión** introduce
   el correo y contraseña del administrador de esa base para habilitar las acciones.
   Las cuentas no se crean automáticamente y no hay una contraseña predeterminada.

Para fijar explícitamente la dirección sugerida:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\Start-Mobile.ps1 -ApiUrl "http://192.168.1.54:8001"
```

Si la base es nueva, crea primero el administrador en una terminal desde backend,
seleccionando la misma base que usa Start-Backend:

```powershell
$env:DATABASE_URL = "sqlite:///./campeonato_prueba_manual.sqlite3"
.\.venv\Scripts\python.exe -m app.bootstrap_admin
```

Si olvidaste sus credenciales, usa `python -m app.reset_admin` con ese mismo Python
y esa base.

### Si no conecta

Abre primero `http://IP_DEL_PC:8001/torneos/` en el navegador del teléfono. Debe
mostrar JSON. Si falla, revisa que el backend esté encendido, la IPv4 sea la
correcta y Windows permita la conexión en tu red privada. Una VPN o una red de
invitados puede impedir la comunicación entre dispositivos.

El QR de Expo y la conexión a la API son conexiones distintas: que el QR funcione
no garantiza que el teléfono pueda llegar al backend.

Se utiliza **SDK 58**, compatible con Expo Go SDK 58 instalado en el teléfono.
El proyecto y Expo Go deben utilizar el mismo SDK. La
[guía de actualización de Expo](https://docs.expo.dev/workflow/upgrading-expo-sdk-walkthrough/)
explica cómo alinear el SDK y sus dependencias.
La [guía de desarrollo](https://docs.expo.dev/get-started/start-developing/) explica
la apertura del QR y la cuenta compartida requerida actualmente en iPhone.

## Ejecución convencional

Con Node.js y npm instalados, desde mobile:

```powershell
npm ci
npm start
```

La URL inicial puede sugerirse mediante `EXPO_PUBLIC_API_URL`; no es un secreto y
no contiene credenciales. La app permite corregirla antes de conectarse.

## Comprobaciones

```powershell
npm run typecheck
npm run export
```

La exportación comprueba los paquetes de Android, iOS y web; no genera un APK ni
un IPA instalable. Expo Go es el método de prueba de esta entrega. Desde Windows
no se ha ejecutado un simulador iOS ni probado un teléfono físico.

La prueba de navegador de la raíz recorre web y la exportación web de la app
contra una base temporal: consulta pública, inicio de sesión, creación de registros,
inscripción, fixture, resultados, campeón y conservación de sesión al recargar.

```powershell
# Desde la raíz; requiere Chrome instalado y el backend con requirements-dev.txt.
npm ci
npm run test:browser
```

Antes de esa prueba, ejecuta `npm run export` en mobile. Las capturas se guardan en
`test-results/`, carpeta excluida de Git. La prueba no usa los datos de tu base manual.
