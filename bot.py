import os
import asyncio
import logging
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from google import genai

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

# Gemini mijozini yaratish
ai_client = genai.Client(api_key=GEMINI_API_KEY)

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
    
    try:
        await update.message.chat.send_action("typing")
    except Exception as e:
        logging.warning(f"Typing xatosi: {e}")

    # Bandlik yuz berganda almashtiriladigan modellar ro'yxati (eng yaxshisidan boshlab)
    models_to_try = [
        'gemini-3.8-flash',
        'gemini-2.5-flash',
        'gemini-2.0-flash',
        'gemini-1.5-flash'
    ]
    
    reply_text = ""
    last_error = ""

    def generate_content_sync(model_name, text):
        return ai_client.models.generate_content(
            model=model_name,
            contents=text,
        )

    loop = asyncio.get_running_loop()

    # Bir nechta modellarni va qayta urinishlarni sinab ko'rish
    for model_name in models_to_try:
        success = False
        for attempt in range(2):  # Har bir model uchun 2 marta urinish
            try:
                response = await loop.run_in_executor(
                    None, 
                    generate_content_sync, 
                    model_name, 
                    user_text
                )
                if response and response.text:
                    reply_text = response.text
                    success = True
                    break
            except Exception as e:
                last_error = str(e)
                logging.warning(f"Model '{model_name}' urinish {attempt+1} xatosi: {e}")
                if "503" in last_error or "429" in last_error:
                    await asyncio.sleep(2 * (attempt + 1))  # Pauza qilib qayta urinish
                else:
                    break  # Agar 503 bo'lmasa, keyingi modelga o'tish
        
        if success:
            break

    if not reply_text:
        reply_text = f"Kechirasiz, serverlar bandligi sababli javob ololmadim. Oxirgi xatolik: {last_error}"

    # Telegram xabar chegarasiga ko'ra bo'lib yuborish
    try:
        if len(reply_text) > 4000:
            for i in range(0, len(reply_text), 4000):
                await update.message.reply_text(reply_text[i:i+4000])
        else:
            await update.message.reply_text(reply_text)
    except Exception as e:
        logging.error(f"Telegramga xabar yuborishda xatolik: {e}")

def main():
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot va Veb-server ishga tushdi...")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
