# 🗺️ Roadmap Belajar CI/CD dari Nol (Homelab STB)

> **Catatan Proyek:** File ini berfungsi sebagai pelacak progres (*progress tracker*). Jika Anda berpindah sesi chat, asisten AI dapat langsung membaca file ini untuk mengetahui status terakhir dan melanjutkan langkah berikutnya.

---

## 📌 Informasi Lingkungan & Server
- **Server:** STB (Set-Top Box) ARM64 (`aarch64`)
- **OS:** Ubuntu 22.04.5 LTS (Jammy Jellyfish) / Kernel Armbian 6.1
- **Memori (RAM):** 2 GB (Available ~1.5 GB)
- **Koneksi:** SSH via Termius & Tailscale (`stb` / `100.117.225.49` / `192.168.137.87`)
- **Proyek Target:** Telegram Chatbot (Python) + Docker + GitHub Actions CI/CD

---

## 📋 Checklist Langkah demi Langkah

### Fase 1: Fondasi Server & Docker
- [x] **1.1. Inspeksi Server:** Pengecekan hardware, OS, dan ketersediaan software di STB.
- [x] **1.2. Clean Uninstall:** Membersihkan instalasi Docker lama agar bisa belajar pasang dari nol.
- [x] **1.3. Fresh Install Docker:** Memasang Docker Engine resmi via `get.docker.com`. *(Selesai - Docker v29.10.0 Community ARM64)*
- [x] **1.4. Verifikasi & Tes Perdana:** Menjalankan `docker run hello-world` dan memahami outputnya.
- [x] **1.5. Konsep Dasar Container:** Memahami siklus hidup container (`docker images`, `docker ps`, `docker ps -a`).

> 💡 **Catatan Penting Keamanan (Docker Privileges & Rootless):**
> Docker menampilkan peringatan bahwa menjalankan Docker dengan user `root` memberikan akses penuh ke sistem host. Di server produksi perusahaan (*production*), disarankan menggunakan *Rootless Mode* atau membatasi izin user. Untuk tahap belajar homelab awal di STB, kita menggunakan mode default agar tidak terhambat kendala izin file (*permission denied*).

---

### Fase 2: Membangun Aplikasi Telegram Bot Mini
- [x] **2.1. Pembuatan Bot Telegram:** Mendaftarkan bot baru via `@BotFather` di aplikasi Telegram dan menyimpan Bot Token dengan aman.
- [x] **2.2. Menulis Kode Bot:** Membuat file aplikasi Python (`app/bot.py`, `app/database.py`) untuk mencatat servis motor, bensin, dan pemantau kuota oli.
- [x] **2.3. Manajemen Dependensi:** Menyiapkan file `requirements.txt`, `.env.example`, dan `.gitignore`.
- [x] **2.4. Resep Kontainer (Dockerfile):** Menulis file `Dockerfile` dan membedah arti setiap baris instruksi.
- [x] **2.5. Orkestrasi (Docker Compose):** Menulis file `docker-compose.yml` untuk mempermudah menjalankan bot di STB.
- [/] **2.6. Tes Manual di STB:** Menjalankan bot pertama kali secara manual di STB agar memahami cara kerja sebelum diotomasi. *(Langkah Saat Ini)*

---

### Fase 3: Pengelolaan Kode dengan Git & GitHub
- [ ] **3.1. Inisialisasi Git:** Menyiapkan git repository di folder `d:\Belajar\HomeLab`.
- [ ] **3.2. Keamanan Kredensial (.gitignore & .env):** Memastikan Token Telegram tidak bocor ke publik.
- [ ] **3.3. Remote Repository:** Membuat repo baru di GitHub dan melakukan `git push` pertama.

---

### Fase 4: Otomasi CI/CD dengan GitHub Actions
- [ ] **4.1. Pemahaman Pipeline CI/CD:** Memahami arsitektur workflow GitHub Actions (.yml).
- [ ] **4.2. Setup GitHub Secrets:** Menyimpan kredensial SSH STB (Host, User, SSH Key) di menu Secrets GitHub secara aman.
- [ ] **4.3. Menulis Workflow (.github/workflows/deploy.yml):**
  - **CI:** Syntax check / validasi kode otomatis di cloud GitHub.
  - **CD:** Otomasi SSH ke STB -> `git pull` -> `docker compose up -d --build`.

---

### Fase 5: Uji Coba Puncak & Pembuktian CI/CD
- [ ] **5.1. Live Update Test:** Mengubah pesan respon bot di laptop (misal: menambahkan perintah `/menu` baru).
- [ ] **5.2. Eksekusi Push:** Menjalankan `git commit` dan `git push` dari laptop.
- [ ] **5.3. Observasi CI/CD:** Memantau proses deploy yang berjalan otomatis di tab GitHub Actions.
- [ ] **5.4. Verifikasi Akhir:** Menguji bot di Telegram HP dan melihat perubahan yang terjadi tanpa menyentuh terminal STB sama sekali!
