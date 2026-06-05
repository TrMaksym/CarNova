import re
import telebot
import os
import urllib3
import requests
import sys
import io
from dotenv import load_dotenv

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
load_dotenv()

bot = telebot.TeleBot(token=os.getenv("TG_BOT"))

AUTO_CACHE = {}


def get_auto_id(endpoint, text, parent_id=None):
    search_text = text.lower().strip()
    url = "https://auto.ria.com/bff/search/public/form/api"
    params = {"device": "desktop", "langId": "4"}

    if parent_id:
        payload = {
            "name": "model",
            "params": {
                "category": 1,
                "brand": int(parent_id),
                "search_type": 1,
                "text": search_text
            }
        }
    else:
        payload = {
            "name": "brand",
            "params": {
                "category": 1,
                "search_type": 1,
                "text": search_text
            }
        }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://auto.ria.com/uk/"
    }

    try:
        response = requests.post(url, params=params, json=payload, headers=headers, timeout=10)
        print(f"LOG: Пошук '{text}' | Статус: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            group_data = data.get("brand") or data.get("model") or []

            items = []
            for group in group_data:
                if isinstance(group, dict) and "items" in group:
                    items.extend(group["items"])

            if items:
                target_item = next((i for i in items if i.get("name", "").lower() == search_text), None)

                if not target_item:
                    target_item = next((i for i in items if search_text in i.get("name", "").lower()), items[0])

                if not target_item:
                    target_item = items[0]

                res_id = target_item.get("id") or target_item.get("value")
                res_name = target_item.get("name")

                print(f"LOG: Успішно розпізнано: {res_name} (ID: {res_id})")
                return res_id, res_name

    except Exception as e:
        print(f"LOG: Помилка виконання: {e}")

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
        return False
    try:
        bot.send_message(chat_id, message_text, parse_mode="HTML")
        return True
    except Exception as e:
        print(f"❌ Помилка відправки: {e}")
        return False


@bot.message_handler(func=lambda message: True)
def handle_text_message(message):
    chat_id = message.chat.id
    user_name = message.from_user.first_name
    text = message.text.strip()

    print(f"LOG: Користувач {user_name} (ID: {chat_id} написав: {text}")

    bot.send_message(chat_id, f"Привіт, {user_name}! Шукаю для тебе: {text}")

    with open("current_filter.txt", "r", encoding="utf-8") as f:
        pass


@bot.message_handler(func=lambda message: True)
def handle_smart_search(message):
    original_text = message.text.strip()
    words = original_text.split()
    if not words:
        return

    brand_query = words[0]
    brand_id, brand_full_name = get_auto_id("brands", brand_query)

    if not brand_id and len(words) > 1:
        brand_query = f"{words[0]} {words[1]}"
        brand_id, brand_full_name = get_auto_id("brands", brand_query)
        if brand_id:
            words.pop(0)

    if not brand_id:
        bot.reply_to(message, "❌ Не впізнав марку. Спробуй написати чіткіше (напр. Audi, BMW).")
        return

    model_id, model_name = "", "Всі моделі"
    if len(words) > 1:
        potential_model = " ".join(words[1:])

        clean_model_query = re.sub(r'\b(199\d|200\d|201\d|202\d)\b', "", potential_model).strip()

        if clean_model_query:
            m_id, m_name = get_auto_id("models", clean_model_query, brand_id)
            if m_id:
                model_id, model_name = m_id, m_name
            else:
                model_name = clean_model_query.upper()

    text_lower = original_text.lower()
    engine_match = re.search(r'(\d[\.,]\d)', text_lower)
    engine = engine_match.group(1).replace(',', '.') if engine_match else ""

    nums = re.findall(r'\d+', text_lower)
    year = next((n for n in nums if 1990 <= int(n) <= 2026), "")
    price = next((n for n in nums if int(n) > 2026), "")

    fuel_map = {"бенз": ("1", "Бензин"), "диз": ("2", "Дизель"), "дт": ("2", "Дизель"), "газ": ("3", "Газ"),
                "електр": ("6", "Електро")}
    fuel, fuel_label = "", ""
    for k, v in fuel_map.items():
        if k in text_lower:
            fuel, fuel_label = v
            break

    filter_data = f"{brand_id}|{model_id}|{year}|{price}|{fuel}|{engine}"

    with open("current_filter.txt", "w", encoding="utf-8") as f:
        f.write(filter_data)

    msg = (
        f"🚀 <b>Радар OmniAuto налаштовано!</b>\n\n"
        f"🚘 Марка: <b>{brand_full_name}</b>\n"
        f"📂 Модель: <b>{model_name}</b>\n"
    )
    if engine: msg += f"⚙️ Мотор: <b>{engine} л.</b>\n"
    if fuel_label: msg += f"⛽ Паливо: <b>{fuel_label}</b>\n"
    if year: msg += f"📅 Рік від: <b>{year}</b>\n"
    if price: msg += f"💰 Ціна до: <b>{price}$</b>\n"

    bot.reply_to(message, msg, parse_mode="HTML")


if __name__ == "__main__":
    print("Bot is starting...")
    bot.infinity_polling()