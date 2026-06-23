/**
 * TLO Electron Preload
 * Exposes safe APIs to renderer via contextBridge
 */
import { contextBridge, ipcRenderer } from 'electron'

contextBridge.exposeInMainWorld('tlo', {
  platform: process.platform,
  isElectron: true,
  version: '1.0.0',

  // File dialogs
  openFileDialog: (options?: any) => ipcRenderer.invoke('dialog:openFile', options),
  saveFileDialog: (options?: any) => ipcRenderer.invoke('dialog:saveFile', options),

  // App info
  getAppPath: () => ipcRenderer.invoke('app:getPath'),
  getVersion: () => ipcRenderer.invoke('app:getVersion'),

  // Notifications
  sendNotification: (title: string, body: string) =>
    ipcRenderer.invoke('notification:send', { title, body }),
})
