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

# Gemini klientini sozlash
ai_client = genai.Client(api_key=GEMINI_API_KEY)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# 1. Flask veb-serverini yaratamiz (Render talabini bajarish uchun)
app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "Bot ishlayapti!"

def run_flask():
    # Render avtomatik beradigan PORT ni o'qiydi
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host="0.0.0.0", port=port)

# 2. Telegram bot funksiyalari
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salom! Men Gemini AI bilan ishlaydigan botman. Savolingizni berishingiz mumkin!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await update.message.chat.send_action("typing")
    
    try:
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_text,
        )
        reply_text = response.text
    except Exception as e:
        reply_text = "Kechirasiz, javob tayyorlashda xatolik yuz berdi."
        print(f"Xatolik: {e}")

    await update.message.reply_text(reply_text)

def main():
    # Flask serverini alohida oqimda (thread) ishga tushiramiz
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()

    # Telegram botni ishga tushiramiz
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot va Veb-server ishga tushdi...")
    app.run_polling()

if __name__ == '__main__':
    main()
