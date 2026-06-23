/**
 * TLO Electron Main Process
 * 借鉴 Aperant electron main — wraps Vue 3 SPA in native desktop shell
 */
import { app, BrowserWindow, shell, Menu, dialog } from 'electron'
import { join } from 'path'
import { existsSync } from 'fs'

const isDev = !app.isPackaged

function createWindow() {
  const win = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 900,
    minHeight: 600,
    title: 'TLO — Testing Lifecycle Orchestrator',
    icon: join(__dirname, '../public/favicon.ico'),
    webPreferences: {
      preload: join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
    // Aperant-style frameless
    titleBarStyle: 'hiddenInset',
    backgroundColor: '#0f1420',
  })

  // Dev: load Vite dev server. Prod: load built files.
  if (isDev) {
    win.loadURL('http://localhost:15173')
    win.webContents.openDevTools({ mode: 'detach' })
  } else {
    win.loadFile(join(__dirname, '../dist/index.html'))
  }

  // External links → browser
  win.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url)
    return { action: 'deny' }
  })

  // Menu bar
  const menu = Menu.buildFromTemplate([
    {
      label: 'TLO',
      submenu: [
        { label: 'About', role: 'about' },
        { type: 'separator' },
        { label: 'Quit', role: 'quit' },
      ],
    },
    {
      label: 'View',
      submenu: [
        { label: 'Reload', role: 'reload' },
        { label: 'DevTools', role: 'toggleDevTools' },
        { type: 'separator' },
        { label: 'Zoom In', role: 'zoomIn' },
        { label: 'Zoom Out', role: 'zoomOut' },
        { label: 'Reset Zoom', role: 'resetZoom' },
      ],
    },
    {
      label: 'Help',
      submenu: [
        {
          label: 'TLO Documentation',
          click: () => shell.openExternal('https://github.com'),
        },
      ],
    },
  ])
  Menu.setApplicationMenu(menu)

  return win
}

app.whenReady().then(() => {
  createWindow()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})
