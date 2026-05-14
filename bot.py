import os
import base64
import tempfile
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp
import uuid

# Aktifkan logging supaya kita boleh lihat log di Render
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Fungsi untuk tulis cookies dari environment variable ke fail sementara
def get_cookiefile():
    cookies_b64 = os.environ.get("YOUTUBE_COOKIES_BASE64")
    if not cookies_b64:
        logger.warning("YOUTUBE_COOKIES_BASE64 tidak ditetapkan. Bot mungkin gagal untuk sesetengah video.")
        return None
    try:
        cookies_data = base64.b64decode(cookies_b64).decode("utf-8")
        # Tulis ke fail sementara
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False)
        tmp.write(cookies_data)
        tmp.close()
        return tmp.name
    except Exception as e:
        logger.error(f"Gagal decode cookies: {e}")
        return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    chat_id = update.message.chat_id

    if "youtube.com" in user_message or "youtu.be" in user_message:
        await update.message.reply_text("🔊 Sedang memproses video YouTube anda...")
        cookiefile_path = get_cookiefile()
        try:
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '0',
                }],
                'outtmpl': f'{uuid.uuid4()}.%(ext)s',
                'quiet': True,
                'no_warnings': True,
                # Tambahan: guna cookies kalau ada
                'cookiefile': cookiefile_path,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(user_message, download=True)
                file_name = ydl.prepare_filename(info_dict)
                if file_name.endswith('.webm'):
                    file_name = file_name[:-5] + '.mp3'
                elif file_name.endswith('.m4a'):
                    file_name = file_name[:-4] + '.mp3'

            with open(file_name, 'rb') as audio:
                await update.message.reply_audio(
                    audio,
                    title=info_dict.get('title', 'YouTube Audio')
                )
            os.remove(file_name)
            logger.info(f"Berjaya: {user_message}")

        except Exception as e:
            logger.error(f"Gagal memproses {user_message}: {e}")
            await update.message.reply_text("❌ Maaf, gagal memproses video. Sila cuba link lain atau cuba sebentar lagi.")
        finally:
            # Padam fail cookies sementara
            if cookiefile_path and os.path.exists(cookiefile_path):
                os.unlink(cookiefile_path)
    else:
        await update.message.reply_text("📎 Sila hantar pautan YouTube yang sah.")

def main():
    TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        raise ValueError("Token bot tidak dijumpai!")

    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Bot sedang berjalan...")
    app.run_polling()

if __name__ == "__main__":
    main()

# Fungsi utama: proses mesej pengguna
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    chat_id = update.message.chat_id

    # Periksa sama ada mesej mengandungi pautan YouTube
    if "youtube.com" in user_message or "youtu.be" in user_message:
        await update.message.reply_text("🔊 Sedang memproses video YouTube anda...")
        try:
            # Tetapan yt-dlp: ekstrak audio terbaik, tukar ke mp3
            ydl_opts = {
                'format': 'bestaudio/best',               # Audio kualiti terbaik
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '0',              # 0 = bitrate paling tinggi (320kbps)
                }],
                'outtmpl': f'{uuid.uuid4()}.%(ext)s',     # Nama fail unik
                'quiet': True,
                'no_warnings': True,
            }

            # Muat turun & tukar audio
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(user_message, download=True)
                # Dapatkan nama fail yang dihasilkan
                file_name = ydl.prepare_filename(info_dict)
                # Pastikan sambungan .mp3
                if file_name.endswith('.webm'):
                    file_name = file_name[:-5] + '.mp3'
                elif file_name.endswith('.m4a'):
                    file_name = file_name[:-4] + '.mp3'

            # Hantar fail audio ke pengguna
            with open(file_name, 'rb') as audio:
                await update.message.reply_audio(
                    audio,
                    title=info_dict.get('title', 'YouTube Audio')
                )
            # Padam fail sementara selepas dihantar
            os.remove(file_name)
            logger.info(f"Berjaya: {user_message}")

        except Exception as e:
            logger.error(f"Gagal memproses {user_message}: {e}")
            await update.message.reply_text("❌ Maaf, gagal memproses video. Sila cuba link lain atau cuba sebentar lagi.")
    else:
        await update.message.reply_text("📎 Sila hantar pautan YouTube yang sah.")

def main():
    # Ambil token dari pembolehubah persekitaran (Environment Variable)
    TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        raise ValueError("Token bot tidak dijumpai! Pastikan TELEGRAM_BOT_TOKEN ditetapkan.")

    # Bina aplikasi bot
    app = Application.builder().token(TOKEN).build()

    # Handler untuk semua mesej teks (kecuali command)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Jalankan bot (mode polling)
    logger.info("Bot sedang berjalan...")
    app.run_polling()

if __name__ == "__main__":
    main()
