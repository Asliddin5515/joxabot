import logging
import speech_recognition as sr
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
import pyttsx3  # Ovoz yaratish uchun pyttsx3 kutubxonasi
from pydub import AudioSegment
import os

# Tokenni bu yerga joylashtiring
TOKEN = '7498184393:AAGzx3L3l9r4P2QVxe79_qbKB8rxgCtWexw'

# Telegram bot uchun logger sozlamalari
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Ovozdan matnga aylantirish funksiyasi
def ovozdan_matnga_aylantirish(audio_path):
    recognizer = sr.Recognizer()

    # Ovozli faylni wav formatida ochish
    with sr.AudioFile(audio_path) as source:
        audio = recognizer.record(source)

    try:
        text = recognizer.recognize_google(audio, language='uz-UZ')
        return text
    except sr.UnknownValueError:
        return "Ovozni tushunmadi."
    except sr.RequestError as e:
        return f"Google Speech servisiga ulanishda xatolik yuz berdi: {e}"

# Matndan ovoz yaratish funksiyasi (pyttsx3 yordamida)
def matndan_ovoza_aylantirish(text):
    engine = pyttsx3.init()
    engine.setProperty('rate', 150)  # Ovozni tezligi
    engine.setProperty('volume', 1)  # Ovozni balandligi
    engine.save_to_file(text, 'output.mp3')  # Ovozli faylni saqlash
    engine.runAndWait()

# Start komandasi (Bot ishlay boshlaganda)
async def start(update: Update, context: CallbackContext):
    keyboard = [
        [
            InlineKeyboardButton("Ovozdan Matnga Aylantirish", callback_data='voice_to_text'),
            InlineKeyboardButton("Matndan Ovozga Aylantirish", callback_data='text_to_voice')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Assalomu alaykum! Tugmalardan birini tanlang:', reply_markup=reply_markup)

# Ovozli xabarni matnga aylantirish
async def handle_voice_message(update: Update, context: CallbackContext):
    # Ovozli xabarni olish
    file = await update.message.voice.get_file()
    
    # Foydalanuvchidan kelgan ovozli faylni yuklab olish
    audio_data = await file.download_as_bytearray()

    # Audio faylni saqlash (ogg formatida)
    with open('user_voice.ogg', 'wb') as f:
        f.write(audio_data)

    # OGG formatini WAV formatiga o'zgartirish
    audio = AudioSegment.from_ogg('user_voice.ogg')
    audio.export('user_voice.wav', format='wav')

    # Ovozli faylni matnga aylantirish
    text = ovozdan_matnga_aylantirish('user_voice.wav')

    # Foydalanuvchiga matnni yuborish
    await update.message.reply_text(f"Matn: {text}")

# Tugma bosilganda ishlash
async def button(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()  # Tugma bosilganda javob qaytarish

    if query.data == 'voice_to_text':
        await query.edit_message_text(text="Iltimos, ovozli xabar yuboring va men uni matnga aylantiraman.")
    elif query.data == 'text_to_voice':
        await query.edit_message_text(text="Iltimos, matn yuboring va men uni ovozga aylantiraman.")

# Foydalanuvchi matn yuborganda uni ovozga aylantirish
async def handle_text_message(update: Update, context: CallbackContext):
    text = update.message.text
    matndan_ovoza_aylantirish(text)
    
    # Ovozli faylni yuborish
    with open('output.mp3', 'rb') as f:
        await update.message.reply_voice(voice=f)
    
    # Ovozli faylni o'chirish (xotira bo'shatish uchun)
    os.remove('output.mp3')

# Xatoliklarni qayta ishlash
def error(update: Update, context: CallbackContext):
    logger.warning('Foydalanuvchi xato qildi: %s', context.error)

# Botni ishga tushirish va buyruqlarni qo'shish
def main():
    # Application va Dispatcher sozlash
    application = Application.builder().token(TOKEN).build()

    # Handlerlar
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice_message))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    
    # CallbackQueryHandler tugmalarni qayta ishlash
    application.add_handler(CallbackQueryHandler(button))

    # Xatoliklar uchun
    application.add_error_handler(error)

    # Botni ishga tushirish
    application.run_polling()

if __name__ == '__main__':
    main()
