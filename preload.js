const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld("api", {
  runAnalysis: (payload) =>
    ipcRenderer.invoke("run-analysis", payload),
  openExternal: (url) => ipcRenderer.invoke('open-external', url),
  getConfig: () =>
    ipcRenderer.invoke("get-config"),
  downloadEnvio: (envio) => ipcRenderer.invoke("download-envio", envio),
});