import telebot
import os
import urllib3
from dotenv import load_dotenv

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

bot = telebot.TeleBot(token=os.getenv("TG_BOT"))


@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(message, "🏎️ CarNova Radar активовано! Я стежу за ринком.")


@bot.message_handler(commands=["status"])
def status(message):
    bot.send_message(message.chat.id, "✅ Радар працює. Останній чек: щойно")


@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, f"Ти написав: {message.text}, але я поки розумію тільки /status та /start")



def send_telegram(message_text):
    chat_id = os.getenv("TG_CHAT_ID")
    if not chat_id:
        print("❌ Помилка: CHAT_ID не знайдено в .env")
        return False
    try:
        bot.send_message(chat_id, message_text, parse_mode="HTML", disable_web_page_preview=False)
        return True
    except Exception as e:
        print(f"❌ Помилка відправки: {e}")
        return False



if __name__ == "__main__":
    print("🤖 Бот заступає на чергування...")

    send_telegram("<b>CarNova Radar</b> успішно запущено в режимі прослуховування!")

    bot.infinity_polling()