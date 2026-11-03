# Probar Copa Colegial en otro PC y presentarla

Esta rama contiene backend, web conectada y aplicación móvil Expo SDK 58.
Los datos y las credenciales de tu computador no se suben a GitHub. En otro PC
la base de prueba comienza vacía y se crea un administrador propio.

## Preparación en otro computador (una sola vez)

Requisitos: Git, Python 3.10 o superior, Node.js 24 LTS (incluye npm) y Expo Go
compatible con SDK 58 en el teléfono. Estos comandos están escritos para Windows.

Si todavía no tienes el repositorio:

```powershell
git clone --branch feat/frontend-app-movil --single-branch https://github.com/ISI-CORP/ISI-2026-2-G11.git
cd ISI-2026-2-G11
```

Si ya lo tienes, desde su carpeta raíz:

```powershell
git fetch origin
git switch feat/frontend-app-movil
```

Prepara las dependencias desde la raíz:

```powershell
py -m venv backend\.venv
.\backend\.venv\Scripts\python.exe -m pip install -r backend\requirements-dev.txt
cd mobile
npm ci
cd ..
```

En una base nueva, crea las tablas y el administrador:

```powershell
cd backend
$env:DATABASE_URL = "sqlite:///./campeonato_prueba_manual.sqlite3"
.\.venv\Scripts\python.exe -m app.create_tables
.\.venv\Scripts\python.exe -m app.bootstrap_admin
cd ..
```

Anota el correo y la contraseña que introduces. Las contraseñas no se muestran
mientras escribes. Si ya existe el administrador y olvidaste el acceso, ejecuta
`app.reset_admin` en lugar de `app.bootstrap_admin`, con ese mismo Python y base.

## Arranque para una presentación

Conecta PC y teléfono a la misma red Wi-Fi. Abre dos terminales PowerShell en
la carpeta raíz `ISI-2026-2-G11`.

**Terminal 1: backend y web**

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\Start-Backend.ps1
```

Deja esa terminal abierta. La web está en http://127.0.0.1:8001. El comando muestra
también la dirección para el teléfono, por ejemplo `http://192.168.1.54:8001`.
La dirección cambia según el PC y la red; usa la que aparece en tu terminal.

**Terminal 2: servidor de desarrollo de la app**

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\Start-Mobile.ps1 -Clear
```

Deja esta terminal abierta también. Aparece el QR de Expo. Abre Expo Go en Android
y escanéalo. En iPhone usa la Cámara y abre el enlace en Expo Go.

Si Expo propone otra interfaz de red, puedes indicar la dirección correcta:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\Start-Mobile.ps1 -Clear -ApiUrl "http://IP_DEL_PC:8001"
```

En la pantalla inicial de la app confirma esa misma dirección y pulsa **Conectar**.
En el teléfono no uses `localhost` ni `127.0.0.1`: esas direcciones apuntan al teléfono.

Si iPhone solicita iniciar sesión en Expo, usa la misma cuenta de Expo en el
teléfono y en el CLI. Detén solo la terminal 2 con Ctrl+C y reinicia añadiendo `-Login`:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\Start-Mobile.ps1 -Clear -Login
```

La cuenta de Expo sirve para abrir el proyecto. El administrador de Copa Colegial
es otra cuenta, la que creaste con `app.bootstrap_admin`.

## Recorrido sugerido para el profesor

1. En la web, abre **Acceso administrador** e inicia sesión.
2. En **Instituciones y staff**, crea un colegio y un entrenador.
3. En **Equipos y jugadores**, crea cuatro equipos y registra jugadores si deseas.
4. En **Campeonatos**, crea uno con **2 grupos y 1 clasificado por grupo**. Inscribe
   los cuatro equipos. Esta configuración permite mostrar dos partidos de grupos y una final.
5. En **Fixture y resultados**, genera el fixture y registra los dos resultados de grupos.
6. En el teléfono, selecciona el mismo campeonato y muestra Fixture, Posiciones y Equipos.
   Puedes deslizar hacia abajo para actualizar inmediatamente.
7. En la web, genera la siguiente ronda y registra la final. Si hay empate,
   introduce ambos resultados de penales con un ganador.
8. Actualiza la app: aparecerán el resultado final y el campeón. Las consultas
   funcionan sin sesión; crear o cambiar datos requiere administrador.

Puedes iniciar sesión también desde **Cuenta** en la app y hacer las operaciones
administrativas allí. Los cambios de web y app se guardan en la misma base.

Para detener todo, pulsa Ctrl+C en cada terminal. Los datos del campeonato permanecen.

Si el teléfono no conecta, abre `http://IP_DEL_PC:8001/torneos/` en su navegador.
Debe aparecer JSON. Si falla, comprueba la IPv4, la conexión Wi-Fi y que Windows
permita la conexión en tu red privada. El acceso al QR y a la API son independientes.

## Verificaciones del código

```powershell
# Desde la raíz
.\backend\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
cd mobile
npm run typecheck
npm run export
cd ..
```

La exportación comprueba paquetes Android/iOS/web, no genera un APK o IPA.
La prueba de navegador requiere Chrome y las dependencias de pruebas de la raíz:

```powershell
npm ci
npm run test:browser
```

Utiliza una base temporal independiente. Los datos de tu demostración no se modifican.
