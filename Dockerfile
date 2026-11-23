# 1. Base Image: Menggunakan Python 3.10 varian slim (sangat ringan, mendukung ARM64 STB)
FROM python:3.10-slim

# 2. Environment Variables:
# - PYTHONDONTWRITEBYTECODE=1 : Mencegah Python membuat file .pyc di kontainer
# - PYTHONUNBUFFERED=1        : Memastikan log langsung tampil di terminal (docker logs) seketika
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 3. Direktori Kerja: Semua perintah selanjutnya dijalankan di dalam folder /app
WORKDIR /app

# 4. Docker Layer Caching:
# Salin requirements.txt terlebih dahulu. Jika kode python berubah tapi requirements tetap,
# Docker tidak perlu mengunduh ulang pustaka (proses build jauh lebih cepat).
COPY requirements.txt .

# 5. Pasang dependensi tanpa menyimpan cache pip agar ukuran image tetap kecil
RUN pip install --no-cache-dir -r requirements.txt

# 6. Salin kode aplikasi
COPY app/ ./app/

# 7. Perintah yang dijalankan ketika kontainer pertama kali di-start
CMD ["python", "app/bot.py"]
