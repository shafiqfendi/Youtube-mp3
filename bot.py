import os
import base64
import tempfile
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp
import uuid

# Aktifkan logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def get_cookiefile():
    cookies_b64 = os.environ.get("YOUTUBE_COOKIES_BASE64")
    if not cookies_b64:
        logger.warning("YOUTUBE_COOKIES_BASE64 tidak ditetapkan. Bot mungkin kena block dengan YouTube.")
        return None
    try:
        cookies_data = base64.b64decode(cookies_b64).decode("utf-8")
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
                    'preferredquality': '192', # Guna 192kbps untuk elak error jika source audio rendah
                }],
                'outtmpl': f'{uuid.uuid4()}.%(ext)s',
                'quiet': True,
                'no_warnings': True,
                'cookiefile': cookiefile_path,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept-Language': 'en-US,en;q=0.9',
                },
                # TRIK PENTING: Tipu YouTube supaya nampak macam request dari Android
                'extractor_args': {
                    'youtube': {
                        'player_client': ['android', 'web']
                    }
                }
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(user_message, download=True)
                file_name = ydl.prepare_filename(info_dict)
                
                # yt-dlp dengan FFmpeg akan automatik tukar extension ke .mp3
                base_name, _ = os.path.splitext(file_name)
                mp3_file = f"{base_name}.mp3"

            if os.path.exists(mp3_file):
                with open(mp3_file, 'rb') as audio:
                    await update.message.reply_audio(
                        audio,
                        title=info_dict.get('title', 'YouTube Audio')
                    )
                os.remove(mp3_file)
                logger.info(f"Berjaya: {user_message}")
            else:
                raise Exception("Fail MP3 tidak dijumpai selepas conversion.")

        except Exception as e:
            logger.error(f"Gagal memproses {user_message}: {e}")
            await update.message.reply_text("❌ Maaf, gagal memproses video. YouTube mungkin block IP, atau video tidak tersedia.")
        
        finally:
            # Cleanup fail cookies
            if cookiefile_path and os.path.exists(cookiefile_path):
                os.unlink(cookiefile_path)
            # Cleanup fail asal (webm/m4a) jika wujud lagi dan gagal delete tadi
            if 'file_name' in locals() and os.path.exists(file_name):
                try: os.remove(file_name)
                except: pass
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
