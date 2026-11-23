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
        [KeyboardButton("/status"), KeyboardButton("/laporan")],
        [KeyboardButton("/riwayat"), KeyboardButton("/help")]
    ],
    resize_keyboard=True
)

# --- Command Handlers ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_authorized(user.id):
        await update.message.reply_text("⛔ Maaf, Anda tidak memiliki akses ke bot pribadi ini.")
        return

    pesan = (
        f"👋 Halo, *{user.first_name}*!\n\n"
        f"Selamat datang di *Bot Catatan Perawatan & Operasional Motor* 🛵💨\n\n"
        f"Bot ini siap membantu mencatat servis, ganti sparepart, isi bensin, "
        f"dan memantau sisa kilometer sebelum ganti oli berikutnya.\n\n"
        f"💡 *Perintah Cepat yang Bisa Digunakan:*\n"
        f"• `/status` - Cek sisa kuota oli & KM motor\n"
        f"• `/km <angka>` - Update kilometer terkini (cth: `/km 25400`)\n"
        f"• `/bensin <biaya> [km]` - Catat bensin (cth: `/bensin 35000`)\n"
        f"• `/servis <km> <biaya> <rincian>` - Catat servis baru\n"
        f"• `/riwayat` - 5 servis terakhir\n"
        f"• `/laporan` - Total pengeluaran bulan ini\n"
        f"• `/help` - Panduan lengkap format perintah\n\n"
        f"🆔 *Telegram User ID Anda:* `{user.id}`\n"
        f"_(Simpan ID ini di file `.env` sebagai `ALLOWED_USER_ID` agar bot aman dari orang lain)_"
    )
    await update.message.reply_text(pesan, parse_mode="Markdown", reply_markup=MAIN_KEYBOARD)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return

    pesan = (
        "📖 *Panduan Penggunaan Bot Motor*\n\n"
        "1️⃣ *Update Kilometer Odometer:*\n"
        "   Format: `/km <angka>`\n"
        "   Contoh: `/km 25450`\n\n"
        "2️⃣ *Catat Bensin:*\n"
        "   Format: `/bensin <biaya_rupiah> [km_opsional]`\n"
        "   Contoh 1: `/bensin 35000`\n"
        "   Contoh 2: `/bensin 50000 25450`\n\n"
        "3️⃣ *Catat Servis / Ganti Part:*\n"
        "   Format: `/servis <km> <biaya_total> <rincian_part>`\n"
        "   Contoh: `/servis 25000 145000 Ganti Oli MPX2, Busi, Kampas Rem`\n\n"
        "4️⃣ *Pengaturan Motor:*\n"
        "   • `/setnama <nama>` - Ubah nama motor (cth: `/setnama Vario 160`)\n"
        "   • `/setoli <km>` - Ubah interval ganti oli (cth: `/setoli 2500`)"
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
        f"🏍️ *Status Motor: {st['motor_name']}*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📍 *KM Terkini:* `{curr_km} KM`\n"
        f"🔧 *Servis Terakhir:* `{last_srv_km} KM`\n"
        f"📝 *Part Terakhir:* {st['last_service_parts']}\n"
        f"🎯 *Interval Ganti Oli:* tiap `{interval} KM`\n\n"
        f"📊 *Status Kondisi Oli:*\n"
        f"{st['alert_status']} | *Sisa: {rem_km} KM*\n"
        f"_{st['alert_msg']}_\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"Ketik `/km <angka>` untuk memperbarui odometer."
    )
    await update.message.reply_text(pesan, parse_mode="Markdown")

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
            f"✅ *KM berhasil diperbarui!* -> `{km_input:,} KM`\n\n"
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
        
        km_text = f" pada KM `{km:,}`" if km else ""
        await update.message.reply_text(
            f"⛽ *Pengisian bensin tercatat!*\nBiaya: *Rp {cost:,}*{km_text}",
            parse_mode="Markdown"
        )
    except ValueError:
        await update.message.reply_text("❌ Biaya atau KM harus berupa angka.", parse_mode="Markdown")

async def servis_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return

    # Butuh minimal 3 argumen: km, biaya, dan rincian part
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

    history = db.get_service_history(limit=5)
    if not history:
        await update.message.reply_text("ℹ️ Belum ada riwayat catatan servis.", parse_mode="Markdown")
        return

    pesan = "📋 *Riwayat 5 Servis Terakhir:*\n━━━━━━━━━━━━━━━━━━\n"
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

    summary = db.get_monthly_expense_summary()
    pesan = (
        f"📊 *Rekapitulasi Pengeluaran ({summary['month']})*\n"
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
    db.set_setting("motor_name", nama)
    await update.message.reply_text(f"✅ Nama motor berhasil diubah menjadi: *{nama}*", parse_mode="Markdown")

async def setoli_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text("⚠️ Contoh: `/setoli 2500` (dalam kilometer)", parse_mode="Markdown")
        return
    try:
        jarak = int(context.args[0].replace(".", "").replace(",", ""))
        db.set_setting("oil_interval_km", str(jarak))
        await update.message.reply_text(f"✅ Interval ganti oli diatur setiap: *{jarak:,} KM*", parse_mode="Markdown")
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
        f"Halo! Sudah akhir pekan nih. Berapa KM speedometer *{st['motor_name']}* sekarang?\n"
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
