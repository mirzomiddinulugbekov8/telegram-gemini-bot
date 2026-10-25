import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from google import genai

# Maxfiy kalitlarni server muhitidan (Environment Variables) o'qiymiz
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

# Gemini klientini sozlash
ai_client = genai.Client(api_key=GEMINI_API_KEY)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

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

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot ishga tushdi...")
    app.run_polling()
