import os
import sqlite3
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple

# Lokasi file database default (bisa diarahkan via env var DATABASE_PATH)
DB_PATH = os.getenv("DATABASE_PATH", "data/motor.db")

def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """Membuka koneksi ke database SQLite dan memastikan direktori ada."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: str = DB_PATH):
    """Inisialisasi tabel-tabel utama jika belum ada."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        # Tabel Pengaturan / Konfigurasi Motor
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        
        # Tabel Riwayat Odometer (KM)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS odometer_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                km INTEGER NOT NULL,
                notes TEXT
            )
        """)
        
        # Tabel Riwayat Servis & Perawatan
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS service_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                km INTEGER NOT NULL,
                parts TEXT NOT NULL,
                cost INTEGER NOT NULL,
                notes TEXT
            )
        """)
        
        # Tabel Riwayat Pengisian Bensin
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fuel_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                km INTEGER,
                cost INTEGER NOT NULL,
                liters REAL,
                notes TEXT
            )
        """)
        
        # Inisialisasi default settings jika belum ada
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('motor_name', 'Motor Kesayangan')")
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('oil_interval_km', '2500')")
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('warning_km', '300')")
        
        conn.commit()

# --- Fungsi Pengaturan ---
def get_setting(key: str, default: str = "") -> str:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row["value"] if row else default

def set_setting(key: str, value: str):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
        conn.commit()

# --- Fungsi Odometer (KM) ---
def add_km(km: int, notes: str = ""):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO odometer_logs (km, notes) VALUES (?, ?)", (km, notes))
        conn.commit()

def get_latest_km() -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT km, recorded_at FROM odometer_logs ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        return dict(row) if row else None

# --- Fungsi Servis ---
def add_service(km: int, parts: str, cost: int, notes: str = ""):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO service_logs (km, parts, cost, notes) VALUES (?, ?, ?, ?)",
            (km, parts, cost, notes)
        )
        # Otomatis catat juga sebagai update KM terbaru
        cursor.execute("INSERT INTO odometer_logs (km, notes) VALUES (?, ?)", (km, f"Saat servis: {parts}"))
        conn.commit()

def get_latest_service() -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT km, parts, cost, recorded_at, notes FROM service_logs ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        return dict(row) if row else None

def get_service_history(limit: int = 5) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, km, parts, cost, recorded_at, notes FROM service_logs ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        return [dict(row) for row in cursor.fetchall()]

# --- Fungsi Bensin ---
def add_fuel(cost: int, km: Optional[int] = None, liters: Optional[float] = None, notes: str = ""):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO fuel_logs (km, cost, liters, notes) VALUES (?, ?, ?, ?)",
            (km, cost, liters, notes)
        )
        if km:
            cursor.execute("INSERT INTO odometer_logs (km, notes) VALUES (?, ?)", (km, "Saat isi bensin"))
        conn.commit()

# --- Fungsi Ringkasan Status & Biaya ---
def get_motor_status() -> Dict[str, Any]:
    motor_name = get_setting("motor_name", "Motor Saya")
    oil_interval = int(get_setting("oil_interval_km", "2500"))
    warning_threshold = int(get_setting("warning_km", "300"))
    
    latest_km_data = get_latest_km()
    latest_service_data = get_latest_service()
    
    current_km = latest_km_data["km"] if latest_km_data else 0
    last_service_km = latest_service_data["km"] if latest_service_data else 0
    last_service_parts = latest_service_data["parts"] if latest_service_data else "Belum ada catatan"
    
    # Hitung pemakaian KM sejak servis terakhir
    km_since_service = max(0, current_km - last_service_km)
    remaining_km = oil_interval - km_since_service
    
    if remaining_km <= 0:
        alert_status = "🔴 OVERDUE"
        alert_msg = f"Sudah melewati jadwal servis sejauh {abs(remaining_km):,} KM! Segera ganti oli."
    elif remaining_km <= warning_threshold:
        alert_status = "🟡 PERHATIAN"
        alert_msg = f"Tersisa {remaining_km:,} KM lagi menuju jadwal servis ganti oli."
    else:
        alert_status = "🟢 AMAN"
        alert_msg = f"Kondisi aman, sisa {remaining_km:,} KM menuju ganti oli."
        
    return {
        "motor_name": motor_name,
        "current_km": current_km,
        "last_service_km": last_service_km,
        "last_service_parts": last_service_parts,
        "last_service_date": latest_service_data["recorded_at"] if latest_service_data else "-",
        "oil_interval": oil_interval,
        "km_since_service": km_since_service,
        "remaining_km": remaining_km,
        "alert_status": alert_status,
        "alert_msg": alert_msg
    }

def get_monthly_expense_summary() -> Dict[str, Any]:
    """Menghitung total pengeluaran servis dan bensin bulan ini."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Biaya servis bulan ini
        cursor.execute("""
            SELECT COALESCE(SUM(cost), 0) as total_service, COUNT(id) as count_service
            FROM service_logs
            WHERE strftime('%Y-%m', recorded_at) = strftime('%Y-%m', 'now')
        """)
        serv = cursor.fetchone()
        
        # Biaya bensin bulan ini
        cursor.execute("""
            SELECT COALESCE(SUM(cost), 0) as total_fuel, COUNT(id) as count_fuel
            FROM fuel_logs
            WHERE strftime('%Y-%m', recorded_at) = strftime('%Y-%m', 'now')
        """)
        fuel = cursor.fetchone()
        
        total_service = serv["total_service"]
        total_fuel = fuel["total_fuel"]
        grand_total = total_service + total_fuel
        
        return {
            "month": datetime.now().strftime("%B %Y"),
            "total_service": total_service,
            "count_service": serv["count_service"],
            "total_fuel": total_fuel,
            "count_fuel": fuel["count_fuel"],
            "grand_total": grand_total
        }
