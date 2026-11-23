import os
import pytest
import tempfile
from app import database as db

@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch):
    """Fixture QA: Membuat database SQLite sementara yang bersih untuk setiap sesi pengujian."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        test_db_path = tmp.name
    
    # Arahkan DATABASE_PATH ke database isolasi sementara
    monkeypatch.setenv("DATABASE_PATH", test_db_path)
    db.init_db(test_db_path)
    
    yield
    
    # Bersihkan file database sementara setelah tes selesai
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

# ========================================================
# SUITE 1: Pengujian Master Kendaraan (Multi-Vehicle)
# ========================================================

def test_tambah_kendaraan_baru():
    """QA-TC-01: Memastikan kendaraan baru berhasil disimpan dan muncul di daftar."""
    sukses = db.add_vehicle(plate_number="D 5678 NMAX", model="Yamaha NMAX", oil_interval_km=3000)
    assert sukses is True

    semua_motor = db.get_all_vehicles()
    plat_terdaftar = [m["plate_number"] for m in semua_motor]
    assert "D 5678 NMAX" in plat_terdaftar

def test_ganti_kendaraan_aktif():
    """QA-TC-02: Memastikan fungsi switch motor aktif berjalan sesuai ekspektasi."""
    db.add_vehicle("B 9999 VAR", "Honda Vario 160", 2500)
    
    # Ganti ke motor baru
    hasil = db.set_active_plate("B 9999 VAR")
    assert hasil is True
    assert db.get_active_plate() == "B 9999 VAR"

def test_ganti_kendaraan_tidak_dikenal_harus_gagal():
    """QA-TC-03: Negative Test - Memilih plat fiktif harus mengembalikan False."""
    hasil = db.set_active_plate("ZZ 9999 FAKE")
    assert hasil is False

# ========================================================
# SUITE 2: Pengujian Logika Bisnis & Perhitungan Sisa Oli
# ========================================================

def test_status_oli_kondisi_aman():
    """QA-TC-04: Sisa KM oli > threshold 300 KM harus berstatus 🟢 AMAN."""
    plat = "B 1234 BEAT"
    db.set_active_plate(plat)
    
    # Catat servis di KM 10.000 (interval bawaan 2.500 KM)
    db.add_service(km=10000, parts="Oli MPX2", cost=55000, plate_number=plat)
    # Catat update odometer di KM 11.000 (pemakaian baru 1.000 KM)
    db.add_km(km=11000, plate_number=plat)
    
    status = db.get_motor_status(plat)
    # Sisa kuota oli seharusnya: 2.500 - (11.000 - 10.000) = 1.500 KM
    assert status["remaining_km"] == 1500
    assert status["alert_status"] == "🟢 AMAN"

def test_status_oli_kondisi_perhatian():
    """QA-TC-05: Sisa KM oli <= 300 KM harus memicu status 🟡 PERHATIAN."""
    plat = "B 1234 BEAT"
    db.set_active_plate(plat)
    
    db.add_service(km=10000, parts="Oli MPX2", cost=55000, plate_number=plat)
    # Odometer 12.300 KM (pemakaian 2.300 KM, sisa 200 KM <= 300 KM)
    db.add_km(km=12300, plate_number=plat)
    
    status = db.get_motor_status(plat)
    assert status["remaining_km"] == 200
    assert status["alert_status"] == "🟡 PERHATIAN"

def test_status_oli_kondisi_overdue():
    """QA-TC-06: Pemakaian melewati interval harus memicu status 🔴 OVERDUE."""
    plat = "B 1234 BEAT"
    db.set_active_plate(plat)
    
    db.add_service(km=10000, parts="Oli MPX2", cost=55000, plate_number=plat)
    # Odometer 12.700 KM (pemakaian 2.700 KM, lewat 200 KM)
    db.add_km(km=12700, plate_number=plat)
    
    status = db.get_motor_status(plat)
    assert status["remaining_km"] == -200
    assert status["alert_status"] == "🔴 OVERDUE"
