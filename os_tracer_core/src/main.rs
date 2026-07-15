use rusqlite::{Connection, Result};
use std::env;
use std::fs;
use std::path::Path;
use std::process::Command;
use chrono::Local;
use walkdir::WalkDir;

struct LogEntry {
    timestamp: String,
    message: String,
}

// Khởi tạo cơ sở dữ liệu lưu trữ hoạt động hệ thống
fn init_db(db_path: &str) -> Result<Connection> {
    let conn = Connection::open(db_path)?;
    conn.execute(
        "CREATE TABLE IF NOT EXISTS system_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            message TEXT NOT NULL
        )",
        [],
    )?;
    Ok(conn)
}

// Quét file cực nhanh bằng WalkDir thay thế cho lệnh `find` CLI của OS
fn find_files(search_path: &str, target_name: &str) -> Vec<String> {
    let mut matched_files = Vec::new();
    let target_lower = target_name.to_lowercase();
    
    for entry in WalkDir::new(search_path).into_iter().filter_map(|e| e.ok()) {
        if entry.file_type().is_file() {
            if let Some(file_name) = entry.file_name().to_str() {
                if file_name.to_lowercase().contains(&target_lower) {
                    matched_files.push(entry.path().display().to_string());
                }
            }
        }
    }
    matched_files
}

// Lấy hoạt động thực tế từ journalctl và lưu trữ vào SQLite nội bộ
fn capture_journal_logs(conn: &Connection, since: &str) -> Result<()> {
    let output = Command::new("journalctl")
        .args(&["--since", since, "-n", "30", "--no-pager", "-q"])
        .output();

    if let Ok(out) = output {
        let log_content = String::from_utf8_lossy(&out.stdout);
        let timestamp = Local::now().format("%Y-%m-%d %H:%M:%S").to_string();
        
        if !log_content.trim().is_empty() {
            conn.execute(
                "INSERT INTO system_logs (timestamp, message) VALUES (?1, ?2)",
                [&timestamp, &log_content.to_string()],
            )?;
        }
    }
    Ok(())
}

#[tokio::main]
async fn main() -> Result<()> {
    let args: Vec<String> = env::args().collect();
    // Đường dẫn DB tĩnh nằm trong storage của RAG để Python đọc chéo dữ liệu
    let db_path = "./rag/local_rag_storage/system_memory.db";
    let conn = init_db(db_path)?;

    if args.len() > 1 {
        match args[1].as_str() {
            "--find" => {
                if args.len() > 2 {
                    let results = find_files("./", &args[2]);
                    for file in results {
                        println!("{}", file);
                    }
                }
            }
            "--daemon" => {
                println!("🚀 Daemon Rust đang chạy ngầm để giám sát kernel hệ thống...");
                loop {
                    let _ = capture_journal_logs(&conn, "10 minutes ago");
                    // Chạy ngầm lập lịch ngủ mỗi 5 phút quét log 1 lần vô cùng tiết kiệm tài nguyên
                    tokio::time::sleep(tokio::time::Duration::from_secs(300)).await;
                }
            }
            _ => println!("Sai tham số. Sử dụng --find <tên_file> hoặc --daemon"),
        }
    } else {
        println!("Vui lòng cung cấp cờ thực thi (--find hoặc --daemon)");
    }

    Ok(())
}

