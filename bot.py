import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from google import genai
from flask import Flask
import threading

# Maxfiy kalitlar
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

# Gemini klientini to'g'ri sozlash
ai_client = genai.Client(api_key=GEMINI_API_KEY)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Flask serveri (Render uchun)
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
    
    try:
        # Yangi genai kutubxonasi uchun to'g'ri chaqiruv
        response = ai_client.models.generate_content(
            model='gemini-3.8-flash',
            contents=user_text
        )
        reply_text = response.text
    except Exception as e:
        # Agar xatolik bo'lsa, uni chatning o'ziga yozib chiqaradi (aniqlab olish uchun)
        reply_text = f"Xatolik yuz berdi: {str(e)}"
        print(f"ANIQ XATOLIK: {e}")

    await update.message.reply_text(reply_text)

def main():
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot va Veb-server ishga tushdi...")
    app.run_polling()

if __name__ == '__main__':
    main()
