// TLO Platform — Tauri v2 Desktop Shell
// Replaces Electron shell (2026-06-25). Python backend runs as sidecar.
//
// Build: cargo tauri build
// Dev:   cargo tauri dev

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::Manager;

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_opener::init())
        .setup(|app| {
            #[cfg(debug_assertions)]
            {
                let window = app.get_webview_window("main").unwrap();
                window.open_devtools();
            }
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running TLO Platform");
}
