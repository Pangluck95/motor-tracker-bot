import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

# Memastikan folder app/ dikenali oleh Python path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.append(CURRENT_DIR)

try:
    from app import database as db
except ImportError:
    import database as db

# Memuat file environment variable (.env)
load_dotenv()

# Konfigurasi Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Konfigurasi Token dan Akses
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_USER_ID = os.getenv("ALLOWED_USER_ID")  # Opsional: batasi hanya Anda yang bisa pakai

def is_authorized(user_id: int) -> bool:
    """Mengecek apakah user berhak berinteraksi dengan bot."""
    if not ALLOWED_USER_ID:
        return True  # Jika belum disetel di .env, izinkan sementara
    return str(user_id) == str(ALLOWED_USER_ID).strip()

# Keyboard menu praktis di bawah chat
MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        [KeyboardButton("/status"), KeyboardButton("/motor")],
        [KeyboardButton("/riwayat"), KeyboardButton("/laporan")],
        [KeyboardButton("/help"), KeyboardButton("/ping")]
    ],
    resize_keyboard=True
)

# --- Command Handlers ---

async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Perintah uji coba CI/CD untuk mengecek status bot & server."""
    if not is_authorized(update.effective_user.id):
        return

    waktu_server = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pesan = (
        f"🏓 *PONG!*\n\n"
        f"🚀 *Status:* Bot aktif dan berjalan normal!\n"
        f"🏠 *Environment:* Homelab STB (Armbian ARM64)\n"
        f"⚡ *Deployment:* Otomatis via GitHub Actions CI/CD\n"
        f"🕒 *Waktu Server:* `{waktu_server}`\n\n"
        f"Pembaruan kode dari laptop berhasil ter-deploy tanpa sentuh terminal STB! ✨"
    )
    await update.message.reply_text(pesan, parse_mode="Markdown")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_authorized(user.id):
        await update.message.reply_text("⛔ Maaf, Anda tidak memiliki akses ke bot pribadi ini.")
        return

    pesan = (
        f"👋 Halo, *{user.first_name}*!\n\n"
        f"Selamat datang di *Bot Catatan Perawatan & Operasional Motor* 🛵💨\n"
        f"⚡ _(Mendukung Multi-Kendaraan & CI/CD Homelab STB)_\n\n"
        f"Bot ini siap membantu mencatat servis, ganti sparepart, isi bensin, "
        f"dan memantau sisa kilometer sebelum ganti oli berikutnya.\n\n"
        f"🛵 *Manajemen Kendaraan:*\n"
        f"• `/motor` - Lihat daftar motor & motor aktif\n"
        f"• `/pilihmotor <plat>` - Ganti motor yang dipantau\n"
        f"• `/tambahmotor <plat>, <jenis>` - Daftarkan motor baru\n\n"
        f"💡 *Perintah Operasional Motor Aktif:*\n"
        f"• `/status` - Cek sisa kuota oli & KM motor aktif\n"
        f"• `/km <angka>` - Update kilometer terkini (cth: `/km 25400`)\n"
        f"• `/bensin <biaya> [km]` - Catat bensin (cth: `/bensin 35000`)\n"
        f"• `/servis <km> <biaya> <rincian>` - Catat servis baru\n"
        f"• `/riwayat` - 5 servis terakhir\n"
        f"• `/laporan` - Total pengeluaran bulan ini\n"
        f"• `/ping` - Cek status bot & pembuktian CI/CD\n"
        f"• `/help` - Panduan lengkap format perintah\n\n"
        f"🆔 *Telegram User ID Anda:* `{user.id}`\n"
        f"_(Simpan ID ini di file `.env` sebagai `ALLOWED_USER_ID` agar bot aman dari orang lain)_"
    )
    await update.message.reply_text(pesan, parse_mode="Markdown", reply_markup=MAIN_KEYBOARD)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return

    pesan = (
        "📖 *Panduan Penggunaan Bot Motor Multi-Kendaraan*\n\n"
        "1️⃣ *Manajemen Kendaraan:*\n"
        "   • `/motor` - Lihat semua motor yang terdaftar\n"
        "   • `/pilihmotor <plat>` - Beralih motor aktif (cth: `/pilihmotor B 1234 BEAT`)\n"
        "   • `/tambahmotor <plat>, <jenis>` - Tambah motor (cth: `/tambahmotor B 1234 ABC, Honda Beat`)\n\n"
        "2️⃣ *Update Kilometer Odometer:*\n"
        "   Format: `/km <angka>`\n"
        "   Contoh: `/km 25450`\n\n"
        "3️⃣ *Catat Bensin:*\n"
        "   Format: `/bensin <biaya_rupiah> [km_opsional]`\n"
        "   Contoh 1: `/bensin 35000`\n"
        "   Contoh 2: `/bensin 50000 25450`\n\n"
        "4️⃣ *Catat Servis / Ganti Part:*\n"
        "   Format: `/servis <km> <biaya_total> <rincian_part>`\n"
        "   Contoh: `/servis 25000 145000 Ganti Oli MPX2, Busi, Kampas Rem`\n\n"
        "5️⃣ *Pengaturan & Utilitas:*\n"
        "   • `/setnama <nama>` - Ubah nama/tipe motor aktif\n"
        "   • `/setoli <km>` - Ubah interval ganti oli motor aktif\n"
        "   • `/ping` - Uji respon bot & info server CI/CD"
    )
    await update.message.reply_text(pesan, parse_mode="Markdown")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return

    st = db.get_motor_status()
    
    # Format angka ribuan
    curr_km = f"{st['current_km']:,}"
    last_srv_km = f"{st['last_service_km']:,}"
    rem_km = f"{st['remaining_km']:,}"
    interval = f"{st['oil_interval']:,}"

    pesan = (
        f"🏍️ *Status Kendaraan Aktif*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🛵 *Tipe:* {st['motor_name']}\n"
        f"🆔 *Plat Nomor:* `{st['plate_number']}`\n"
        f"📍 *KM Terkini:* `{curr_km} KM`\n"
        f"🔧 *Servis Terakhir:* `{last_srv_km} KM`\n"
        f"📝 *Part Terakhir:* {st['last_service_parts']}\n"
        f"🎯 *Interval Ganti Oli:* tiap `{interval} KM`\n\n"
        f"📊 *Status Kondisi Oli:*\n"
        f"{st['alert_status']} | *Sisa: {rem_km} KM*\n"
        f"_{st['alert_msg']}_\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"Ketik `/motor` untuk ganti motor atau `/km <angka>` untuk update odometer."
    )
    await update.message.reply_text(pesan, parse_mode="Markdown")

async def motor_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Melihat daftar semua kendaraan yang terdaftar dan motor aktif saat ini."""
    if not is_authorized(update.effective_user.id):
        return

    vehicles = db.get_all_vehicles()
    if not vehicles:
        await update.message.reply_text("ℹ️ Belum ada kendaraan terdaftar. Gunakan `/tambahmotor <plat>, <model>`", parse_mode="Markdown")
        return

    pesan = "🛵 *Daftar Kendaraan Anda:*\n━━━━━━━━━━━━━━━━━━\n"
    for idx, v in enumerate(vehicles, 1):
        status_aktif = " *(AKTIF ✅)*" if v.get("is_active") else ""
        pesan += (
            f"{idx}. *{v['model']}*{status_aktif}\n"
            f"   🆔 Plat: `{v['plate_number']}`\n"
            f"   🎯 Interval Oli: `{v['oil_interval_km']:,} KM`\n\n"
        )
    pesan += (
        "━━━━━━━━━━━━━━━━━━\n"
        "💡 *Tips Perintah:*\n"
        "• `/pilihmotor <plat>` - Beralih ke motor lain\n"
        "• `/tambahmotor <plat>, <jenis>` - Tambah motor baru"
    )
    await update.message.reply_text(pesan, parse_mode="Markdown")

async def tambahmotor_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menambahkan atau memperbarui data kendaraan."""
    if not is_authorized(update.effective_user.id):
        return

    if not context.args:
        await update.message.reply_text(
            "⚠️ *Format Tambah Motor:*\n"
            "`/tambahmotor <plat>, <jenis motor> [interval_oli]`\n\n"
            "Contoh:\n"
            "`/tambahmotor B 1234 ABC, Honda Beat`\n"
            "`/tambahmotor D 5678 NMX, Yamaha NMAX 3000`",
            parse_mode="Markdown"
        )
        return

    raw_text = " ".join(context.args)
    interval_km = 2500

    # Cek pemisah koma atau strip
    if "," in raw_text:
        parts = [p.strip() for p in raw_text.split(",", 1)]
        plate = parts[0]
        model_part = parts[1]
    elif "-" in raw_text:
        parts = [p.strip() for p in raw_text.split("-", 1)]
        plate = parts[0]
        model_part = parts[1]
    else:
        # Jika tanpa tanda baca: kata pertama = plat, sisanya = model
        plate = context.args[0]
        model_part = " ".join(context.args[1:])

    # Cek apakah di akhir model_part ada angka interval oli
    model_tokens = model_part.split()
    if model_tokens and model_tokens[-1].isdigit() and len(model_tokens) > 1:
        interval_km = int(model_tokens[-1])
        model_name = " ".join(model_tokens[:-1])
    else:
        model_name = model_part

    if not model_name:
        await update.message.reply_text("❌ Harap sertakan nama/jenis motor. Contoh: `/tambahmotor B 1234 ABC, Honda Beat`", parse_mode="Markdown")
        return

    db.add_vehicle(plate_number=plate, model=model_name, oil_interval_km=interval_km)
    
    await update.message.reply_text(
        f"✅ *Kendaraan Berhasil Disimpan!*\n\n"
        f"🏍️ *Jenis:* {model_name}\n"
        f"🆔 *Plat Nomor:* `{plate.upper()}`\n"
        f"🎯 *Interval Oli:* `{interval_km:,} KM`\n\n"
        f"Gunakan `/pilihmotor {plate.upper()}` untuk menjadikannya motor aktif.",
        parse_mode="Markdown"
    )

async def pilihmotor_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Memilih kendaraan aktif yang sedang dipantau."""
    if not is_authorized(update.effective_user.id):
        return

    if not context.args:
        await update.message.reply_text(
            "⚠️ Harap masukkan nomor plat kendaraan.\n"
            "Contoh: `/pilihmotor B 1234 BEAT`\n"
            "Ketik `/motor` untuk melihat daftar plat yang tersimpan.",
            parse_mode="Markdown"
        )
        return

    plate_input = " ".join(context.args).strip()
    success = db.set_active_plate(plate_input)
    
    if success:
        st = db.get_motor_status()
        await update.message.reply_text(
            f"🔄 *Kendaraan Aktif Berhasil Diganti!*\n\n"
            f"🏍️ *Motor:* {st['motor_name']}\n"
            f"🆔 *Plat Nomor:* `{st['plate_number']}`\n\n"
            f"Sekarang perintah `/status`, `/km`, `/bensin`, dan `/servis` akan mencatat ke motor ini.",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            f"❌ Kendaraan dengan plat `{plate_input.upper()}` tidak ditemukan.\n"
            f"Ketik `/motor` untuk melihat daftar kendaraan terdaftar.",
            parse_mode="Markdown"
        )

async def km_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return

    if not context.args:
        await update.message.reply_text(
            "⚠️ Masukkan angka kilometer.\nContoh: `/km 25450`",
            parse_mode="Markdown"
        )
        return

    try:
        km_input = int(context.args[0].replace(".", "").replace(",", ""))
        db.add_km(km_input, notes="Manual update via chat")
        
        st = db.get_motor_status()
        pesan = (
            f"✅ *KM berhasil diperbarui!* -> `{km_input:,} KM`\n"
            f"🛵 *Motor Aktif:* {st['motor_name']} (`{st['plate_number']}`)\n\n"
            f"Sisa kuota oli saat ini: *{st['remaining_km']:,} KM* ({st['alert_status']})"
        )
        await update.message.reply_text(pesan, parse_mode="Markdown")
    except ValueError:
        await update.message.reply_text("❌ Kilometer harus berupa angka bulat. Contoh: `/km 25450`", parse_mode="Markdown")

async def bensin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return

    if not context.args:
        await update.message.reply_text(
            "⚠️ Format: `/bensin <biaya> [km]`\nContoh: `/bensin 35000` atau `/bensin 35000 25450`",
            parse_mode="Markdown"
        )
        return

    try:
        cost = int(context.args[0].replace(".", "").replace(",", ""))
        km = None
        if len(context.args) > 1:
            km = int(context.args[1].replace(".", "").replace(",", ""))

        db.add_fuel(cost=cost, km=km)
        
        st = db.get_motor_status()
        km_text = f" pada KM `{km:,}`" if km else ""
        await update.message.reply_text(
            f"⛽ *Pengisian bensin tercatat!*\n"
            f"🛵 *Motor:* {st['motor_name']} (`{st['plate_number']}`)\n"
            f"💰 Biaya: *Rp {cost:,}*{km_text}",
            parse_mode="Markdown"
        )
    except ValueError:
        await update.message.reply_text("❌ Biaya atau KM harus berupa angka.", parse_mode="Markdown")

async def servis_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return

    if len(context.args) < 3:
        await update.message.reply_text(
            "⚠️ Format: `/servis <km> <biaya> <rincian part>`\n\n"
            "Contoh:\n`/servis 25000 145000 Oli Mesin MPX2, Oli Gardan, Kampas Rem`",
            parse_mode="Markdown"
        )
        return

    try:
        km = int(context.args[0].replace(".", "").replace(",", ""))
        cost = int(context.args[1].replace(".", "").replace(",", ""))
        parts = " ".join(context.args[2:])

        db.add_service(km=km, parts=parts, cost=cost)

        st = db.get_motor_status()
        pesan = (
            f"✅ *Servis Berhasil Dicatat!* 🔧\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🛵 *Motor:* {st['motor_name']} (`{st['plate_number']}`)\n"
            f"📍 *KM Servis:* `{km:,} KM`\n"
            f"💰 *Total Biaya:* `Rp {cost:,}`\n"
            f"🛠️ *Rincian Part:* {parts}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🔄 Counter ganti oli di-reset! Sisa kuota berikutnya: *{st['remaining_km']:,} KM*."
        )
        await update.message.reply_text(pesan, parse_mode="Markdown")
    except ValueError:
        await update.message.reply_text("❌ KM dan Biaya harus berupa angka.", parse_mode="Markdown")

async def riwayat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return

    st = db.get_motor_status()
    history = db.get_service_history(limit=5)
    if not history:
        await update.message.reply_text(
            f"ℹ️ Belum ada riwayat catatan servis untuk *{st['motor_name']}* (`{st['plate_number']}`).",
            parse_mode="Markdown"
        )
        return

    pesan = f"📋 *Riwayat 5 Servis Terakhir ({st['motor_name']} - {st['plate_number']}):*\n━━━━━━━━━━━━━━━━━━\n"
    for idx, item in enumerate(history, 1):
        tgl = item['recorded_at'][:10]
        pesan += (
            f"{idx}. *{tgl}* | `{item['km']:,} KM`\n"
            f"   🛠️ {item['parts']}\n"
            f"   💰 Rp {item['cost']:,}\n\n"
        )
    await update.message.reply_text(pesan, parse_mode="Markdown")

async def laporan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return

    st = db.get_motor_status()
    summary = db.get_monthly_expense_summary()
    pesan = (
        f"📊 *Rekapitulasi Pengeluaran ({summary['month']})*\n"
        f"🛵 *Motor:* {st['motor_name']} (`{st['plate_number']}`)\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"⛽ *Bensin:* Rp {summary['total_fuel']:,} _({summary['count_fuel']}x pengisian)_\n"
        f"🔧 *Servis & Part:* Rp {summary['total_service']:,} _({summary['count_service']}x servis)_\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💰 *Total Biaya Operasional:* *Rp {summary['grand_total']:,}*"
    )
    await update.message.reply_text(pesan, parse_mode="Markdown")

async def setnama_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text("⚠️ Contoh: `/setnama Honda Vario 160`", parse_mode="Markdown")
        return
    nama = " ".join(context.args)
    plate = db.get_active_plate()
    db.add_vehicle(plate_number=plate, model=nama)
    await update.message.reply_text(f"✅ Nama motor aktif (`{plate}`) diubah menjadi: *{nama}*", parse_mode="Markdown")

async def setoli_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text("⚠️ Contoh: `/setoli 2500` (dalam kilometer)", parse_mode="Markdown")
        return
    try:
        jarak = int(context.args[0].replace(".", "").replace(",", ""))
        plate = db.get_active_plate()
        st = db.get_motor_status()
        db.add_vehicle(plate_number=plate, model=st["motor_name"], oil_interval_km=jarak)
        await update.message.reply_text(f"✅ Interval ganti oli untuk `{plate}` diatur setiap: *{jarak:,} KM*", parse_mode="Markdown")
    except ValueError:
        await update.message.reply_text("❌ Jarak harus berupa angka.", parse_mode="Markdown")

# --- Pengingat Otomatis (Weekly Reminder Callback) ---
async def weekly_km_reminder(context: ContextTypes.DEFAULT_TYPE):
    """Pengingat otomatis menanyakan KM motor."""
    admin_id = os.getenv("ALLOWED_USER_ID")
    if not admin_id:
        return
    
    st = db.get_motor_status()
    pesan = (
        f"⏰ *Pengingat Rutin Kilometer Motor* 🛵\n\n"
        f"Halo! Sudah akhir pekan nih. Berapa KM speedometer *{st['motor_name']}* (`{st['plate_number']}`) sekarang?\n"
        f"KM terakhir tercatat: `{st['current_km']:,} KM`\n\n"
        f"Yuk perbarui dengan mengetik:\n`/km <angka_speedometer>`"
    )
    await context.bot.send_message(chat_id=int(admin_id), text=pesan, parse_mode="Markdown")

def main():
    """Fungsi utama menjalankan bot."""
    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN belum disetel di file .env!")
        print("❌ Error: Harap masukkan TELEGRAM_BOT_TOKEN di file .env terlebih dahulu.")
        return

    # Inisialisasi Database SQLite
    db.init_db()
    logger.info("Database berhasil diinisialisasi.")

    # Membangun Aplikasi Telegram Bot
    app = Application.builder().token(BOT_TOKEN).build()

    # Mendaftarkan Handler Perintah
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("ping", ping_command))
    app.add_handler(CommandHandler("motor", motor_command))
    app.add_handler(CommandHandler("tambahmotor", tambahmotor_command))
    app.add_handler(CommandHandler("pilihmotor", pilihmotor_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("km", km_command))
    app.add_handler(CommandHandler("bensin", bensin_command))
    app.add_handler(CommandHandler("servis", servis_command))
    app.add_handler(CommandHandler("riwayat", riwayat_command))
    app.add_handler(CommandHandler("laporan", laporan_command))
    app.add_handler(CommandHandler("setnama", setnama_command))
    app.add_handler(CommandHandler("setoli", setoli_command))

    # Jadwalkan Reminder Mingguan jika JobQueue aktif
    if app.job_queue and ALLOWED_USER_ID:
        # Jadwalkan setiap hari Minggu jam 08:00 pagi
        import datetime as dt
        app.job_queue.run_daily(
            weekly_km_reminder,
            time=dt.time(hour=8, minute=0, second=0),
            days=(6,) # 6 = Minggu
        )
        logger.info("Job scheduler reminder mingguan aktif.")

    logger.info("Bot Motor sedang berjalan...")
    app.run_polling()

if __name__ == "__main__":
    main()
