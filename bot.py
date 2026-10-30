import os
import asyncio
import logging
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from google import genai

# Atrof-muhit o'zgaruvchilarini olish
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

# Gemini mijozini yaratish
ai_client = genai.Client(api_key=GEMINI_API_KEY)

# Log sozlamalarini to'g'irlash
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "Bot ishlayapti!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host="0.0.0.0", port=port)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salom! Men Gemini AI bilan ishlaydigan botman. Savolingizni berishingiz mumkin!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    
    # Typing effektini yuborish
    try:
        await update.message.chat.send_action("typing")
    except Exception as err:
        logging.warning(f"Typing yuborishda xatolik: {err}")
    
    reply_text = ""
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            # Synch SDK chaqiruvini asinxron oqimga o'tkazamiz (bot muzlab qolmasligi uchun)
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                None,
                lambda: ai_client.models.generate_content(
                    model='gemini-3.8-flash',
                    contents=user_text,
                )
            )
            reply_text = response.text
            break  # Javob muvaffaqiyatli olindi
            
        except Exception as e:
            err_msg = str(e)
            logging.error(f"Urashish {attempt + 1} xatosi: {err_msg}")
            
            if ("503" in err_msg or "429" in err_msg) and attempt < max_retries - 1:
                # time.sleep o'rniga asinxron kutish (bot boshqa foydalanuvchilarni ham to'xtatib qo'ymaydi)
                await asyncio.sleep(2)
                continue
            else:
                reply_text = f"Xatolik yuz berdi: {err_msg}"
                break

    # Agar javob bo'sh kelib qolsa
    if not reply_text:
        reply_text = "Kechirasiz, javob olishda noma'lum xatolik yuz berdi."

    # Telegram xabarining maksimum uzunligi (4096 belgi) bo'yicha bo'lib yuborish
    try:
        if len(reply_text) > 4000:
            for i in range(0, len(reply_text), 4000):
                await update.message.reply_text(reply_text[i:i+4000])
        else:
            await update.message.reply_text(reply_text)
    except Exception as e:
        logging.error(f"Xabarni yuborishda Telegram xatosi: {e}")

def main():
    # Flask serverni alohida thread'da yuritish
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()

    # Telegram botni sozlash
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot va Veb-server ishga tushdi...")
    app.run_polling()

if __name__ == '__main__':
    main()
