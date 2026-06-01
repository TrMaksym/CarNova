import re

import telebot
import os
import urllib3
from dotenv import load_dotenv
import requests

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

bot = telebot.TeleBot(token=os.getenv("TG_BOT"))

def get_id_from_ria(endpoint, text):
    url = f"https://auto.ria.com/api/categories/1/{endpoint}/_search?text={text}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=5).json()
        if response and len(response) > 0:
            return response[0]["value"]
    except:
        pass
    return None

def get_brand_id(brand_name):
    search_text = brand_name.capitalize()

    url = f"https://auto.ria.com/api/categories/1/brands/_search?text={search_text}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=5).json()
        if response and len(response) > 0:
            return response[0]["value"], response[0]["name"]
    except Exception as e:
        print(f"Помилка запиту до API: {e}")

    return None, None


@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(message, "🏎️ CarNova Radar активовано! Я стежу за ринком.")


@bot.message_handler(commands=["status"])
def status(message):
    bot.send_message(message.chat.id, "✅ Радар працює. Останній чек: щойно")


@bot.message_handler(commands=["radar"])
def radar_command(message):
    bot.send_message(
        message.chat.id,
        "📡 <b>Система моніторингу OmniAuto</b>\n\n"
        "🟢 Статус: <i>Активний</i>\n"
        "🚗 Фільтр: <i>Всі нові надходження</i>\n"
        "⏱️ Частота перевірки: <i>30 секунд</i>",
        parse_mode="HTML"
    )

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


@bot.message_handler(func=lambda message: True)
def handle_smart_search(message):
    original_text = message.text.strip()
    words = original_text.split()

    if not words:
        return

    brand_id, brand_full_name = get_brand_id(words[0])

    if not brand_id:
        brand_id, brand_full_name = get_brand_id(words[0].capitalize())

    if not brand_id:
        bot.reply_to(message, "❌ Не впізнав марку. Спробуй написати чіткіше (напр. Audi, BMW, Mercedes).")
        return

    model_id = ""
    model_name = "Всі моделі"
    if len(words) > 1:
        model_url = f"https://auto.ria.com/api/categories/1/marks/{brand_id}/models/_search?text={words[1]}"
        headers = {"User-Agent": "Mozilla/5.0"}
        try:
            m_res = requests.get(model_url, headers=headers, timeout=5).json()
            if m_res:
                model_id = m_res[0]['value']
                model_name = m_res[0]['name']
            else:
                model_name = words[1].upper()
        except:
            model_name = words[1].upper()

    text_lower = original_text.lower()

    engine_match = re.search(r'(\d[\.,]\d)', text_lower)
    engine = engine_match.group(1).replace(',', '.') if engine_match else ""

    nums = re.findall(r'\d+', text_lower)
    year = next((n for n in nums if 1990 <= int(n) <= 2026), "")
    price = next((n for n in nums if int(n) > 2026), "")

    fuel = ""
    fuel_label = ""
    if "бенз" in text_lower:
        fuel, fuel_label = "1", "Бензин"
    elif "диз" in text_lower or "дт" in text_lower:
        fuel, fuel_label = "2", "Дизель"
    elif "газ" in text_lower:
        fuel, fuel_label = "3", "Газ"
    elif "електр" in text_lower:
        fuel, fuel_label = "6", "Електро"

    filter_data = f"{brand_id}|{model_id}|{year}|{price}|{fuel}|{engine}"
    with open("current_filter.txt", "w", encoding="utf-8") as f:
        f.write(filter_data)

    msg = (
        f"🚀 <b>Радар OmniAuto налаштовано!</b>\n\n"
        f"🚘 Марка: <b>{brand_full_name}</b>\n"
        f"📂 Модель: <b>{model_name}</b>\n"
    )
    if engine: msg += f"⚙️ Мотор: <b>{engine}</b>\n"
    if fuel_label: msg += f"⛽ Паливо: <b>{fuel_label}</b>\n"
    if year: msg += f"📅 Рік від: <b>{year}</b>\n"
    if price: msg += f"💰 Ціна до: <b>{price}$</b>\n"

    bot.reply_to(message, msg, parse_mode="HTML")



if __name__ == "__main__":
    print("🤖 Бот заступає на чергування...")

    send_telegram("<b>CarNova Radar</b> успішно запущено в режимі прослуховування!")

    bot.infinity_polling()