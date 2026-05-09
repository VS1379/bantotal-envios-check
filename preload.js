const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
  runAnalysis: (payload) => ipcRenderer.invoke('run-analysis', payload),
});