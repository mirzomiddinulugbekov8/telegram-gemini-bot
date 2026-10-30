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

# Log sozlamalari
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Render / Web-service uxlashining oldini olish uchun Flask server
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
    await update.message.chat.send_action("typing")
    
    reply_text = ""
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            # To'g'ri model nomi ishlatilmoqda
            response = ai_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=user_text,
            )
            reply_text = response.text
            break  # Muvaffaqiyatli javob olindi
        except Exception as e:
            err_msg = str(e)
            if "503" in err_msg and attempt < max_retries - 1:
                # time.sleep o'rniga asyncio.sleep ishlatamiz
                await asyncio.sleep(2)
                continue
            else:
                reply_text = f"Xatolik yuz berdi: {err_msg}"
                logging.error(f"ANIQ XATOLIK: {e}")
                break

    # Telegram xabar uzunligi chegarasi (4096 belgi)
    if len(reply_text) > 4000:
        for i in range(0, len(reply_text), 4000):
            await update.message.reply_text(reply_text[i:i+4000])
    else:
        await update.message.reply_text(reply_text)

def main():
    # Flask serverni alohida oqimda ishga tushirish
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()

    # Telegram botni ishga tushirish
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot va Veb-server ishga tushdi...")
    app.run_polling()

if __name__ == '__main__':
    main()
