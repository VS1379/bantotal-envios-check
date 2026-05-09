require('dotenv').config();

const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    backgroundColor: '#0b0f14',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  mainWindow.loadFile(path.join(__dirname, 'renderer', 'index.html'));
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

/* =========================
IPC: RUN ANALYSIS (PYTHON)
========================= */
ipcMain.handle('run-analysis', async (_, payload) => {
  return new Promise((resolve, reject) => {
    const py = spawn('python', ['main.py', JSON.stringify(payload)]);

    let output = '';
    let errorOutput = '';

    py.stdout.on('data', (data) => {
      const txt = data.toString();
      output += txt;

      // 👇 importante: puede venir en chunks
      if (output.includes('RESULT:')) {
        try {
          const jsonStr = output.split('RESULT:')[1].trim();
          const parsed = JSON.parse(jsonStr);
          resolve(parsed);
        } catch (err) {
          reject('Error parseando JSON de Python: ' + err.message);
        }
      }
    });

    py.stderr.on('data', (data) => {
      errorOutput += data.toString();
    });

    py.on('close', (code) => {
      if (!output.includes('RESULT:')) {
        reject(errorOutput || `Python terminó sin RESULT (code ${code})`);
      }
    });
  });
});

/* =========================
IPC: CONFIG (.env)
========================= */
ipcMain.handle('get-config', async () => {
  return {
    user: process.env.BANTOTAL_USER || '',
    pass: process.env.BANTOTAL_PASS || '',
    rarPassword: process.env.RAR_PASSWORD || '',
  };
});