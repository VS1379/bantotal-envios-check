require('dotenv').config();

const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;

console.log('********************************************************');
console.log('App iniciada. Cargando configuracion...');
console.log('main.js');
console.log('********************************************************');

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
ipcMain.handle("run-analysis", async (_, payload) => {

  console.log("PAYLOAD RECIBIDO");
  console.log(payload);

  return new Promise((resolve, reject) => {

    const py = spawn(
      "python",
      ["main.py", JSON.stringify(payload)],
      {
        env: {
          ...process.env,
          PYTHONIOENCODING: "utf-8"
        }
      }
    );

    let output = "";
    let errorOutput = "";

    py.stdout.on("data", (data) => {

      const txt = data.toString();

      console.log("PYTHON:", txt);

      output += txt;

      if (output.includes("RESULT:")) {

        try {

          const jsonStr = output.split("RESULT:")[1].trim();

          const parsed = JSON.parse(jsonStr);

          resolve(parsed);

        } catch (err) {

          reject(
            "Error parseando JSON de Python: " +
            err.message
          );
        }
      }
    });

    py.stderr.on("data", (data) => {

      const txt = data.toString();

      console.error("PYTHON ERROR:", txt);

      errorOutput += txt;
    });

    py.on("close", (code) => {

      console.log(
        `Python finalizó. Code=${code}`
      );

      if (!output.includes("RESULT:")) {

        reject(
          errorOutput ||
          `Python terminó sin RESULT (code ${code})`
        );
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