// TLO Platform library — Tauri v2 backend logic
// Python sidecar management, tray menu, auto-update stub.

use tauri::Manager;

/// Spawn Python backend sidecar when app starts.
/// Uses tauri-plugin-shell for cross-platform process management.
#[tauri::command]
fn get_backend_status() -> String {
    // Check if Python backend is reachable
    match ureq::get("http://localhost:8000/health").call() {
        Ok(resp) => {
            let body = resp.into_string().unwrap_or_default();
            format!("backend: {}", body)
        }
        Err(e) => format!("backend unreachable: {}", e),
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![get_backend_status])
        .run(tauri::generate_context!())
        .expect("error while running TLO Platform");
}
