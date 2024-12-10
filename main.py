import telebot
import requests
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# Токен вашего бота
TOKEN = '8006512955:AAF73BS-1stSho8V-qWvoI-Mn7oQXC-9dAA'
bot = telebot.TeleBot(TOKEN)

# Команда /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
  bot.reply_to(message, "Привет! Отправь своё местоположение, чтобы узнать адрес.")
  send_location_request(message)

# Отправка кнопки для запроса местоположения
def send_location_request(message):
  markup = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
  location_button = KeyboardButton("📍 Отправить местоположение", request_location=True)
  markup.add(location_button)
  bot.send_message(message.chat.id, "Пожалуйста, отправь своё местоположение:", reply_markup=markup)

# Обработка получения геолокации
@bot.message_handler(content_types=['location'])
def handle_location(message):
  if message.location is not None:
    latitude = message.location.latitude
    longitude = message.location.longitude

    address = get_address_from_coordinates(latitude, longitude)
    if address:
      bot.reply_to(message, f"Ваше местоположение: {address}")
    else:
      bot.reply_to(message, "Не удалось определить адрес по координатам. Попробуйте ещё раз.")

def get_address_from_coordinates(lat, lon):
  try:
    url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=18&addressdetails=1"
    headers = {"User-Agent": "TelegramBot/1.0 (example@example.com)"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
      data = response.json()
      if "address" in data:
        return data["display_name"]
        return None
  except Exception as e:
    print(f"Ошибка получения адреса: {e}")
    return None

# Запуск бота
if __name__ == "__main__":
  print("Бот запущен.")
  bot.infinity_polling()
