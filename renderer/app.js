//APP.JS
/* ── Parser de envíos (idéntico al prototipo aprobado) ────── */
function extraerEnvios(texto) {
  const resultados = [];

  // Formato 1: bloques con "Envíos:"
  const fmt1Blocks = texto.split(/(?=\[IBTBSE-)/);
  for (const bloque of fmt1Blocks) {
    const ticketMatch = bloque.match(/\[?(IBTBSE-\d+)\]?/);
    if (!ticketMatch) continue;
    const enviosMatch = bloque.match(/Env[ií]os?:\s*([\d\s\-]+)/i);
    if (!enviosMatch) continue;
    const nums = enviosMatch[1].match(/\d+/g)?.map(Number) || [];
    if (!nums.length) continue;
    const descMatch = bloque.match(/\]?\s*([^\n\[]+?)(?:\s*-\s*Jira)?[\n$]/);
    const desc = descMatch ? descMatch[1].trim() : '';
    resultados.push({ ticket: ticketMatch[1], formato: 1, desc, nums });
  }

  const ticketsFmt1 = new Set(resultados.map(r => r.ticket));

  // Formato 2: separado por __
  const lineas = texto.split('\n');

  for (const linea of lineas) {
    const l = linea.trim();
    if (!l || l.startsWith('Clave')) continue;

    const match = l.match(/(IBTBSE-\d+)\s+(.+?)\s+([\d\s\-]+)$/);
    if (!match) continue;

    const [, ticket, descRaw, enviosRaw] = match;
    const nums = enviosRaw.match(/\d+/g)?.map(Number) || [];

    resultados.push({
      ticket,
      formato: 3,
      desc: descRaw.trim(),
      nums
    });
  }

  return resultados;
}

/* ── Estado global ──────────────────────────────────────────── */
let parsedData = [];   // [{ticket, formato, desc, nums}]
let todosNumeros = [];   // lista plana de todos los nros
let resultados = [];   // [{envio, ticket, progreso, sqls, hasDrop, hasCreate, skipped}]
let filtroActivo = 'all';

/* ── Elementos del DOM ──────────────────────────────────────── */
const inputText = document.getElementById('inputText');
const parsedPreview = document.getElementById('parsedPreview');
const enviosCount = document.getElementById('enviosCount');
const btnRun = document.getElementById('btnRun');
const logPanel = document.getElementById('logPanel');
const logBody = document.getElementById('logBody');
const spinner = document.getElementById('spinner');
const statusDot = document.getElementById('statusDot');
const statusText = document.getElementById('statusText');

/* ── Navegación ─────────────────────────────────────────────── */
document.querySelectorAll('.nav-item').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('view-' + btn.dataset.view).classList.add('active');
  });
});

/* ── Parser en tiempo real ──────────────────────────────────── */
inputText.addEventListener('input', actualizarPreview);

function actualizarPreview() {
  const texto = inputText.value.trim();
  parsedData = extraerEnvios(texto);
  todosNumeros = [...new Set(parsedData.flatMap(r => r.nums))];

  parsedPreview.innerHTML = '';
  if (!todosNumeros.length) {
    enviosCount.textContent = '— envíos detectados';
    btnRun.disabled = true;
    return;
  }

  enviosCount.textContent = `${todosNumeros.length} envío${todosNumeros.length !== 1 ? 's' : ''} detectado${todosNumeros.length !== 1 ? 's' : ''}`;

  // Mostrar chips (máx 12 para no saturar)
  const visible = todosNumeros.slice(0, 12);
  visible.forEach(n => {
    const chip = document.createElement('span');
    chip.className = 'pv-chip';
    chip.textContent = n;
    parsedPreview.appendChild(chip);
  });
  if (todosNumeros.length > 12) {
    const chip = document.createElement('span');
    chip.className = 'pv-chip';
    chip.textContent = `+${todosNumeros.length - 12} más`;
    parsedPreview.appendChild(chip);
  }

  btnRun.disabled = false;
}

/* ── Cargar variables ────────────────────────────────────────── */
window.addEventListener('DOMContentLoaded', async () => {
  if (window.api) {
    const cfg = await window.api.getConfig();

    document.getElementById('cfgUrl').textContent = cfg.url || '-';
    document.getElementById('cfgRar').textContent = cfg.rarPassword || '-';
    document.getElementById('inputUser').value = cfg.user || '';
    document.getElementById('inputPass').value = cfg.pass || '';
  }
});

/* ── Correr análisis ────────────────────────────────────────── */
btnRun.addEventListener('click', async () => {
  if (!todosNumeros.length) return;

  // Reset UI
  logBody.innerHTML = '';
  logPanel.style.display = '';
  spinner.classList.add('active');
  btnRun.disabled = true;
  setStatus('running', 'Analizando…');

  // Escuchar progreso en tiempo real
  if (window.api) {
    window.api.offProgress();
    window.api.onProgress(line => agregarLog(line));
  }

  try {
    let data;

    if (window.api) {
      // Modo Electron: llamar a Python via IPC
      data = await window.api.runAnalysis({
        envios: todosNumeros
      });
    } else {
      // Modo dev browser: simular resultado
      data = simularResultado(todosNumeros, parsedData);
    }

    resultados = data;
    mostrarDashboard(res);
    setStatus('done', 'Listo');
    agregarLog('✓ Análisis completado', 'ok');

    // Ir automáticamente al dashboard
    document.querySelector('[data-view="dashboard"]').click();

  } catch (err) {
    agregarLog('✗ Error: ' + (err.error || JSON.stringify(err)), 'err');
    setStatus('error', 'Error');
  } finally {
    spinner.classList.remove('active');
    btnRun.disabled = false;
  }
});

/* ── Log helpers ────────────────────────────────────────────── */
function agregarLog(msg, tipo = '') {
  const div = document.createElement('div');
  div.className = 'log-line ' + tipo;

  // Inferir tipo por contenido si no se especificó
  if (!tipo) {
    if (/✓|OK|100%|skip/i.test(msg)) div.className = 'log-line ok';
    if (/warn|atención/i.test(msg)) div.className = 'log-line warn';
    if (/error|✗|fail/i.test(msg)) div.className = 'log-line err';
    if (/skip|skipping/i.test(msg)) div.className = 'log-line skip';
  }

  div.textContent = msg;
  logBody.appendChild(div);
  logBody.scrollTop = logBody.scrollHeight;
}

/* ── Status sidebar ─────────────────────────────────────────── */
function setStatus(estado, txt) {
  statusDot.className = 'status-dot ' + estado;
  statusText.textContent = txt;
}

/* ── Dashboard ──────────────────────────────────────────────── */
function mostrarDashboard(data) {
  const total = data.length;
  const skipped = data.filter(r => r.skipped).length;
  const conSql = data.filter(r => r.sqls && r.sqls.length > 0).length;
  const conDdl = data.filter(r => r.hasDrop || r.hasCreate).length;

  document.getElementById('st-total').textContent = total;
  document.getElementById('st-skip').textContent = skipped;
  document.getElementById('st-sql').textContent = conSql;
  document.getElementById('st-ddl').textContent = conDdl;

  const subtitle = `${total} envíos · ${conDdl} con DROP/CREATE TABLE`;
  document.getElementById('dashSubtitle').textContent = subtitle;

  document.getElementById('statsRow').style.display = '';
  document.getElementById('resultsWrap').style.display = '';
  document.getElementById('emptyState').style.display = 'none';

  renderTabla(data);

  // Listener de búsqueda
  document.getElementById('searchInput').oninput = filtrarTabla;
}

let tablaData = [];

function renderTabla(data) {
  tablaData = data;
  filtrarTabla();
}

function filtrarTabla() {
  const q = (document.getElementById('searchInput')?.value || '').toLowerCase();

  const filas = tablaData.filter(r => {
    const matchText = !q
      || String(r.envio).includes(q)
      || (r.ticket || '').toLowerCase().includes(q);

    const matchFilter =
      filtroActivo === 'all' ? true :
        filtroActivo === 'ddl' ? (r.hasDrop || r.hasCreate) :
          filtroActivo === 'sql' ? (r.sqls && r.sqls.length > 0) :
            filtroActivo === 'skip' ? r.skipped : true;

    return matchText && matchFilter;
  });

  const tbody = document.getElementById('resultsTbody');
  tbody.innerHTML = '';

  if (!filas.length) {
    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:var(--text3);padding:2rem;font-size:13px;">Sin resultados para este filtro.</td></tr>';
    return;
  }

  for (const r of filas) {
    const tr = document.createElement('tr');

    const pct = r.progreso ?? 0;
    const progressHtml = r.skipped
      ? `<span class="tag tag-skip">100% — skip</span>`
      : `<div style="display:flex;align-items:center;gap:8px">
           <div class="progress-bar"><div class="progress-fill${pct === 100 ? ' full' : ''}" style="width:${pct}%"></div></div>
           <span style="font-family:var(--mono);font-size:11px;color:var(--text2)">${pct}%</span>
         </div>`;

    const sqlsHtml = r.skipped
      ? '<span style="color:var(--text3);font-size:12px">—</span>'
      : (r.sqls && r.sqls.length
        ? r.sqls.map(s => `<span class="tag tag-ok">${s}</span>`).join(' ')
        : '<span style="color:var(--text3);font-size:12px">ninguno</span>');

    const dropHtml = r.skipped ? '—' : (r.hasDrop ? '<span class="tag tag-yes">SÍ</span>' : '<span class="tag tag-no">NO</span>');
    const createHtml = r.skipped ? '—' : (r.hasCreate ? '<span class="tag tag-yes">SÍ</span>' : '<span class="tag tag-no">NO</span>');

    tr.innerHTML = `
      <td><span class="envio-num">#${r.envio}</span></td>
      <td>${r.ticket ? `<span class="ticket-chip">${r.ticket}</span>` : '<span style="color:var(--text3)">—</span>'}</td>
      <td>${progressHtml}</td>
      <td>${sqlsHtml}</td>
      <td>${dropHtml}</td>
      <td>${createHtml}</td>
    `;
    tbody.appendChild(tr);
  }
}

/* ── Filtro pills ───────────────────────────────────────────── */
function setFilter(f, btn) {
  filtroActivo = f;
  document.querySelectorAll('.pill').forEach(p => p.classList.remove('active'));
  btn.classList.add('active');
  filtrarTabla();
}

/* ── Simulación para dev sin Electron ──────────────────────── */
function simularResultado(numeros, parsed) {
  // Mapa envio → ticket
  const ticketMap = {};
  for (const p of parsed) {
    for (const n of p.nums) ticketMap[n] = p.ticket;
  }

  return numeros.map(n => {
    const skipped = Math.random() > 0.6;
    const hasSql = !skipped && Math.random() > 0.4;
    const hasDrop = hasSql && Math.random() > 0.5;
    const hasCr = hasSql && Math.random() > 0.5;
    return {
      envio: n,
      ticket: ticketMap[n] || null,
      progreso: skipped ? 100 : Math.floor(Math.random() * 90) + 5,
      skipped,
      sqls: hasSql ? [`${n}_Script_1.sql`] : [],
      hasDrop,
      hasCreate: hasCr,
    };
  });
}
async function buscarUno() {
  const nro = document.getElementById('singleEnvio').value;
  if (!nro) return;

  setStatus('running', 'Consultando…');

  const res = await window.api.runAnalysis({
    envios: [Number(nro)]
  });

  mostrarDashboard(res);
}

document.getElementById('btnBuscar')?.addEventListener('click', async () => {
  const nro = document.getElementById('singleEnvio').value;

  if (!nro) return;

  const res = await window.api.runAnalysis({
    envios: [Number(nro)]
  });
  const r = res[0];

  document.getElementById('singleResult').innerHTML = `
    <pre>${JSON.stringify(r, null, 2)}</pre>
  `;
});