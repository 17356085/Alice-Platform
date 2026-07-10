/**
 * Cross-platform folder picker.
 * - Tauri desktop: native dialog → returns real filesystem path
 * - Browser: showDirectoryPicker / webkitdirectory fallback → returns path or null
 *
 * Returns the selected folder path, or null if cancelled / unavailable.
 * In web browsers without the File System Access API, the caller should
 * handle the null case and prompt the user to type the path manually.
 */

// Non-standard browser APIs (Chromium + Tauri)
declare global {
  interface Window {
    showDirectoryPicker?: () => Promise<{ path?: string; name: string }>
    __TAURI_INTERNALS__?: unknown
  }
}
interface HTMLInputElement {
  files?: FileList | null
  webkitdirectory?: boolean
}

export async function pickFolder(): Promise<string | null> {
  // ── Tauri native dialog (real filesystem paths) ──────────────
  if ('__TAURI_INTERNALS__' in window) {
    try {
      const { open } = await import('@tauri-apps/plugin-dialog')
      const selected = await open({
        directory: true,
        multiple: false,
        title: '选择文件夹',
      })
      if (selected && typeof selected === 'string') {
        return selected
      }
      return null // user cancelled
    } catch {
      // Tauri dialog failed — try web fallback below
    }
  }

  // ── Web: File System Access API (Chromium) ───────────────────
  if ('showDirectoryPicker' in window) {
    try {
      const handle = await window.showDirectoryPicker?.()
      // handle.path is non-standard (Chromium only); handle.name is always available
      return handle?.path || null
    } catch {
      return null // user cancelled
    }
  }

  // ── Web: legacy webkitdirectory fallback (Chromium) ──────────
  return new Promise((resolve) => {
    const input = document.createElement('input')
    input.type = 'file'
    input.webkitdirectory = true
    input.onchange = (e: Event) => {
      const files = (e.target as HTMLInputElement).files
      if (files?.length) {
        // webkitRelativePath gives relative path; not a full filesystem path
        // but at least we get the folder name
        const folder = files[0].webkitRelativePath.split('/')[0]
        resolve(folder)
      } else {
        resolve(null)
      }
    }
    input.oncancel = () => resolve(null)
    input.click()
  })
}
