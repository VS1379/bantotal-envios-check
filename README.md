# Analizador de Envíos — Bantotal SGR

App desktop (Electron + Python + Playwright) para analizar envíos del SGR Bantotal.

## Setup

### 1. Dependencias Node
```bash
cd envios-app
npm install
```

### 2. Dependencias Python
```bash
pip install playwright rarfile
playwright install chromium
```

> **Importante:** `rarfile` requiere `unrar` instalado en el sistema:
> - **Windows:** instalar [WinRAR](https://www.win-rar.com/) o bajar
>   [unrar.exe standalone](https://www.rarlab.com/rar_add.htm) y agregarlo al PATH
> - **Linux:** `sudo apt install unrar`
> - **macOS:** `brew install rar`

### 3. Credenciales (opcional)
Renombrá `.env.example` a `.env` y completá:
```
```
Si no, las podés ingresar directamente en la UI cada vez.

### 4. Correr la app
```bash
npm start
```

---

## Estructura

```
envios-app/
├── .env                 ← credenciales
├── .gitignore
├── main.js              ← proceso principal Electron (IPC)
├── preload.js           ← bridge seguro renderer ↔ main
├── package.json
├── renderer/
│   ├── index.html       ← UI principal
│   ├── style.css        ← estilos dark
│   └── app.js           ← parser de texto + lógica UI + dashboard
└── python/
    ├── main.py          ← entry point (args → JSON result)
    ├── browser.py       ← Playwright: login, scraping, descarga RAR
    └── sql_checker.py   ← detecta DROP TABLE / CREATE TABLE
```

---

## Flujo completo

```
[UI] Pegar texto (fmt 1, fmt 2 o mezclado)
       ↓ parser JS extrae números + tickets
[UI] Click "Iniciar análisis"
       ↓ IPC → main.js → spawn python main.py
[Python] Login en SGREnvios (#/login)
       ↓ por cada número de envío:
       ↓ navegar a #/index/aplicar?Id={nro}
       ↓ leer #barra_progreso style="width: X%"
       ↓ si X == 100 → skip
       ↓ si X < 100  → leer tabla ng-repeat="objeto in objetos"
       ↓              → filtrar td[ng-bind="objeto.DetEnvObj"] con .sql
       ↓              → click a[ng-click*="descargarZip"][ng-click*="'N'"]
       ↓              → descomprimir RAR (pwd: EsteroArg#2024$)
       ↓              → leer archivos en Scripts/*.sql
       ↓              → detectar DROP TABLE / CREATE TABLE
[Python] Imprimir RESULT:{json}
[UI] Dashboard: stats + tabla filtrable por DROP/CREATE/SQL/skip
```

---

## Test sin UI (línea de comando)
```bash
cd python
python main.py --numeros 9200,9202,8144 --usuario xxxx --password xxxx
```
