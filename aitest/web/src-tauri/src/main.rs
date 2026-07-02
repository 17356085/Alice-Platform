// TLO Platform — Tauri v2 Desktop Shell
// Starts Python backend, then navigates WebView to localhost:8000.
// Avoids tauri.localhost DNS hijacking (common in China).

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::io::Write;
use std::net::TcpStream;
use std::process::{Child, Command};
use std::sync::Mutex;
use std::thread;
use std::time::Duration;
use tauri::Manager;

struct BackendProcess(Mutex<Option<Child>>);

impl Drop for BackendProcess {
    fn drop(&mut self) {
        if let Ok(mut guard) = self.0.lock() {
            if let Some(ref mut child) = *guard {
                let _ = child.kill();
                let _ = child.wait();
                tlo_log("Python backend killed");
            }
        }
    }
}

fn tlo_log(msg: &str) {
    let tmp = std::env::temp_dir().join("tlo-platform.log");
    let ts = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs();
    let _ = std::fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open(&tmp)
        .and_then(|mut f| writeln!(f, "[{}] {}", ts, msg));
}

fn start_backend() -> Option<Child> {
    tlo_log("Starting Python backend...");
    let python = if cfg!(target_os = "windows") { "python" } else { "python3" };
    // CWD must be parent of aitest/ to avoid aitest.platform shadowing stdlib platform
    let cwd = if cfg!(target_os = "windows") {
        std::path::Path::new("D:/Desktop/Alice")
    } else {
        std::path::Path::new(".")
    };
    match Command::new(python)
        .args(["-m", "aitest.server.main"])
        .current_dir(cwd)
        .stdout(std::process::Stdio::null())
        .stderr(std::process::Stdio::null())
        .spawn()
    {
        Ok(child) => {
            tlo_log(&format!("Python backend pid={}", child.id()));
            Some(child)
        }
        Err(e) => {
            tlo_log(&format!("Python start failed: {}", e));
            None
        }
    }
}

fn wait_for_backend(timeout_s: u64) -> bool {
    for i in 1..=timeout_s {
        if TcpStream::connect_timeout(
            &"127.0.0.1:8000".parse().unwrap(),
            Duration::from_secs(1),
        )
        .is_ok()
        {
            tlo_log(&format!("Backend ready after {}s", i));
            return true;
        }
        thread::sleep(Duration::from_secs(1));
    }
    tlo_log("Backend did not start in time");
    false
}

fn main() {
    tlo_log("TLO Platform starting");

    let builder = tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_opener::init());

    let builder = builder.setup(|app| {
        tlo_log("Setup hook running");
        let child = start_backend();
        app.manage(BackendProcess(Mutex::new(child)));

        // Navigate to Python backend once it's ready
        // Workaround: tauri.localhost DNS hijacked in China → ERR_CONNECTION_REFUSED
        let handle = app.handle().clone();
        thread::spawn(move || {
            if wait_for_backend(30) {
                thread::sleep(Duration::from_millis(500));
                if let Some(window) = handle.get_webview_window("main") {
                    tlo_log("Navigating to http://localhost:8000");
                    let _ = window.eval("window.location.replace('http://localhost:8000')");
                }
            }
        });

        tlo_log("Setup complete");
        Ok(())
    });

    builder
        .run(tauri::generate_context!())
        .expect("error while running TLO Platform");
}
