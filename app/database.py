import os
import sqlite3
from datetime import datetime
from typing import Optional, Dict, Any, List

# Lokasi file database default (dinamis membaca env var DATABASE_PATH)
def get_db_path() -> str:
    return os.getenv("DATABASE_PATH", "data/motor.db")

def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Membuka koneksi ke database SQLite dan memastikan direktori ada."""
    target_path = db_path or get_db_path()
    dir_name = os.path.dirname(target_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: Optional[str] = None):
    """Inisialisasi tabel-tabel utama jika belum ada."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        # 1. Tabel Pengaturan / Konfigurasi
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        
        # 2. Tabel Master Kendaraan (Multi-Motor)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vehicles (
                plate_number TEXT PRIMARY KEY,
                model TEXT NOT NULL,
                oil_interval_km INTEGER DEFAULT 2500,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 3. Tabel Riwayat Odometer (KM)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS odometer_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                plate_number TEXT,
                km INTEGER NOT NULL,
                notes TEXT
            )
        """)
        
        # 4. Tabel Riwayat Servis & Perawatan
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS service_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                plate_number TEXT,
                km INTEGER NOT NULL,
                parts TEXT NOT NULL,
                cost INTEGER NOT NULL,
                notes TEXT
            )
        """)
        
        # 5. Tabel Riwayat Pengisian Bensin
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fuel_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                plate_number TEXT,
                km INTEGER,
                cost INTEGER NOT NULL,
                liters REAL,
                notes TEXT
            )
        """)
        
        # Migrasi kolom plate_number jika tabel lama sudah ada sebelumnya
        for tbl in ["odometer_logs", "service_logs", "fuel_logs"]:
            try:
                cursor.execute(f"ALTER TABLE {tbl} ADD COLUMN plate_number TEXT")
            except sqlite3.OperationalError:
                pass  # Kolom sudah ada
        
        # Inisialisasi default settings & motor perdana jika belum ada
        cursor.execute("""
            INSERT OR IGNORE INTO vehicles (plate_number, model, oil_interval_km)
            VALUES ('B 1234 BEAT', 'Honda Beat', 2500)
        """)
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('active_plate', 'B 1234 BEAT')")
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('warning_km', '300')")
        
        conn.commit()

# --- Fungsi Pengaturan Umum ---
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

# --- Fungsi Multi-Kendaraan (Vehicles) ---
def add_vehicle(plate_number: str, model: str, oil_interval_km: int = 2500) -> bool:
    """Mendaftarkan kendaraan baru."""
    clean_plate = plate_number.strip().upper()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO vehicles (plate_number, model, oil_interval_km) VALUES (?, ?, ?)",
            (clean_plate, model.strip(), oil_interval_km)
        )
        conn.commit()
    # Jika belum ada plate yang aktif, set motor ini sebagai aktif
    if not get_setting("active_plate"):
        set_active_plate(clean_plate)
    return True

def get_all_vehicles() -> List[Dict[str, Any]]:
    """Mengambil seluruh daftar kendaraan yang tersimpan beserta penanda aktif."""
    active_plate = get_active_plate()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT plate_number, model, oil_interval_km FROM vehicles ORDER BY created_at ASC")
        rows = cursor.fetchall()
        result = []
        for r in rows:
            item = dict(r)
            item["is_active"] = (item["plate_number"] == active_plate)
            result.append(item)
        return result

def get_active_plate() -> str:
    """Mendapatkan nomor plat kendaraan yang sedang aktif."""
    return get_setting("active_plate", "B 1234 BEAT")

def set_active_plate(plate_number: str) -> bool:
    """Mengganti kendaraan yang sedang aktif dipantau."""
    clean_plate = plate_number.strip().upper()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT plate_number FROM vehicles WHERE plate_number = ?", (clean_plate,))
        if not cursor.fetchone():
            return False  # Plat tidak ditemukan
    set_setting("active_plate", clean_plate)
    return True

# --- Fungsi Odometer (KM) ---
def add_km(km: int, notes: str = "", plate_number: Optional[str] = None):
    plate = (plate_number or get_active_plate()).strip().upper()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO odometer_logs (plate_number, km, notes) VALUES (?, ?, ?)",
            (plate, km, notes)
        )
        conn.commit()

def get_latest_km(plate_number: Optional[str] = None) -> Optional[Dict[str, Any]]:
    plate = (plate_number or get_active_plate()).strip().upper()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT km, recorded_at FROM odometer_logs WHERE plate_number = ? OR plate_number IS NULL ORDER BY id DESC LIMIT 1",
            (plate,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

# --- Fungsi Servis ---
def add_service(km: int, parts: str, cost: int, notes: str = "", plate_number: Optional[str] = None):
    plate = (plate_number or get_active_plate()).strip().upper()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO service_logs (plate_number, km, parts, cost, notes) VALUES (?, ?, ?, ?, ?)",
            (plate, km, parts, cost, notes)
        )
        # Otomatis catat juga sebagai update KM terbaru untuk motor ini
        cursor.execute(
            "INSERT INTO odometer_logs (plate_number, km, notes) VALUES (?, ?, ?)",
            (plate, km, f"Saat servis: {parts}")
        )
        conn.commit()

def get_latest_service(plate_number: Optional[str] = None) -> Optional[Dict[str, Any]]:
    plate = (plate_number or get_active_plate()).strip().upper()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT km, parts, cost, recorded_at, notes FROM service_logs WHERE plate_number = ? OR plate_number IS NULL ORDER BY id DESC LIMIT 1",
            (plate,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

def get_service_history(limit: int = 5, plate_number: Optional[str] = None) -> List[Dict[str, Any]]:
    plate = (plate_number or get_active_plate()).strip().upper()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, km, parts, cost, recorded_at, notes FROM service_logs WHERE plate_number = ? OR plate_number IS NULL ORDER BY id DESC LIMIT ?",
            (plate, limit)
        )
        return [dict(row) for row in cursor.fetchall()]

# --- Fungsi Bensin ---
def add_fuel(cost: int, km: Optional[int] = None, liters: Optional[float] = None, notes: str = "", plate_number: Optional[str] = None):
    plate = (plate_number or get_active_plate()).strip().upper()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO fuel_logs (plate_number, km, cost, liters, notes) VALUES (?, ?, ?, ?, ?)",
            (plate, km, cost, liters, notes)
        )
        if km:
            cursor.execute(
                "INSERT INTO odometer_logs (plate_number, km, notes) VALUES (?, ?, ?)",
                (plate, km, "Saat isi bensin")
            )
        conn.commit()

# --- Fungsi Ringkasan Status & Biaya ---
def get_motor_status(plate_number: Optional[str] = None) -> Dict[str, Any]:
    active_plate = (plate_number or get_active_plate()).strip().upper()
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT plate_number, model, oil_interval_km FROM vehicles WHERE plate_number = ?", (active_plate,))
        v_row = cursor.fetchone()
        
    if v_row:
        motor_name = v_row["model"]
        oil_interval = v_row["oil_interval_km"]
        plate_str = v_row["plate_number"]
    else:
        motor_name = "Honda Beat"
        oil_interval = 2500
        plate_str = active_plate
        
    warning_threshold = int(get_setting("warning_km", "300"))
    
    latest_km_data = get_latest_km(active_plate)
    latest_service_data = get_latest_service(active_plate)
    
    current_km = latest_km_data["km"] if latest_km_data else 0
    last_service_km = latest_service_data["km"] if latest_service_data else 0
    last_service_parts = latest_service_data["parts"] if latest_service_data else "Belum ada catatan"
    
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
        "plate_number": plate_str,
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

def get_monthly_expense_summary(plate_number: Optional[str] = None) -> Dict[str, Any]:
    """Menghitung total pengeluaran servis dan bensin bulan ini."""
    plate = (plate_number or get_active_plate()).strip().upper()
    with get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COALESCE(SUM(cost), 0) as total_service, COUNT(id) as count_service
            FROM service_logs
            WHERE (plate_number = ? OR plate_number IS NULL)
              AND strftime('%Y-%m', recorded_at) = strftime('%Y-%m', 'now')
        """, (plate,))
        serv = cursor.fetchone()
        
        cursor.execute("""
            SELECT COALESCE(SUM(cost), 0) as total_fuel, COUNT(id) as count_fuel
            FROM fuel_logs
            WHERE (plate_number = ? OR plate_number IS NULL)
              AND strftime('%Y-%m', recorded_at) = strftime('%Y-%m', 'now')
        """, (plate,))
        fuel = cursor.fetchone()
        
        total_service = serv["total_service"]
        total_fuel = fuel["total_fuel"]
        grand_total = total_service + total_fuel
        
        return {
            "plate_number": plate,
            "month": datetime.now().strftime("%B %Y"),
            "total_service": total_service,
            "count_service": serv["count_service"],
            "total_fuel": total_fuel,
            "count_fuel": fuel["count_fuel"],
            "grand_total": grand_total
        }
