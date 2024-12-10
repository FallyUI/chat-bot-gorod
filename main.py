import telebot
import requests
from decimal import Decimal
from telebot import types
from geopy.geocoders import Nominatim
from geopy.exc import GeopyError

API_2GIS_KEY = '0289f404-c7ac-4866-a2ca-2068601a43b3'
API_TELEGRAM_TOKEN = "8006512955:AAF73BS-1stSho8V-qWvoI-Mn7oQXC-9dAA"

bot = telebot.TeleBot(API_TELEGRAM_TOKEN)

def get_location_by_coordinates(latitude: float, longitude: float) -> dict:
    try:
        geolocator = Nominatim(user_agent="location-finder")
        location = geolocator.reverse((latitude, longitude), language='ru')

        if location and location.raw:
            address = location.raw.get("address", {})
            street = address.get("road", "Не найдена")
            house_number = address.get("house_number", "Не найден")
            city = address.get("city") or address.get("town") or address.get("village", "Не найдено")
            return {
                "street": street,
                "city": city,
                "house_number": house_number
            }
        else:
            return {"error": "Местоположение не найдено"}
    except GeopyError as e:
        return {"error": str(e)}

def find_places_in_2gis(query, lat, lon, radius=1000):
    url = "https://catalog.api.2gis.com/3.0/items"
    params = {
        "q": query,
        "point": f"{lon},{lat}",
        "radius": radius,
        "fields": "items.point,items.full_address",
        "key": API_2GIS_KEY,
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        places = []
        for item in data.get("result", {}).get("items", []):
            place = {
                "name": item.get("name", "Неизвестное место"),
                "address": item.get("full_address", "Адрес не указан"),
                "lat": item.get("point", {}).get("lat"),
                "lon": item.get("point", {}).get("lon"),
            }
            places.append(place)
        return places
    except Exception as e:
        print(f"Ошибка при работе с API 2ГИС: {e}")
        return []

@bot.message_handler(commands=['start'])
def start_message(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    find_places = types.KeyboardButton('Найти места')
    markup.add(find_places)
    
    bot.send_message(message.chat.id, 'Приветствую!\n'
                                      'Это городской бот, который поможет найти интересные места рядом с Вами.\n'
                                      'Для начала работы, Вы можете использовать кнопки ниже!', reply_markup=markup)

@bot.message_handler(func=lambda message: message.text in ['Найти места', 'Попробовать ещё раз!'])
def your_places_to_find(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    interests = ["🖥 Технологии", "🎮 Игры", "📚 Книги", "🎵 Музыка", "🍕 Еда", "🏃 Спорт", "🏛 Музеи"]
    buttons = [types.KeyboardButton(interest) for interest in interests]
    markup.add(*buttons)
    bot.send_message(message.chat.id, "Выбери свой интерес:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text in ["🖥 Технологии", "🎮 Игры", "📚 Книги", "🎵 Музыка", "🍕 Еда", "🏃 Спорт", "🏛 Музеи"])
def handle_interest(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    location_button = types.KeyboardButton('📍 Отправить местоположение', request_location=True)
    markup.add(location_button)

    bot.send_message(message.chat.id, f'Вы выбрали интерес: {message.text}. Теперь отправьте сюда Ваше местоположение, чтобы я мог найти ближайшие места.', reply_markup=markup)
    bot.register_next_step_handler(message, lambda msg: handle_search(msg, message.text))

def handle_search(message, query):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    restart_button = types.KeyboardButton('Попробовать ещё раз!')
    markup.add(restart_button)
    
    radius = 1000

    if message.location is not None:
        lat = message.location.latitude
        lon = message.location.longitude

    bot.send_message(message.chat.id, f"Ищу места по теме: '{query}' в радиусе {radius} метров...")
    places = find_places_in_2gis(query, lat, lon, radius)

    if not places:
        bot.send_message(message.chat.id, f"Ничего не найдено по запросу '{query}' в радиусе {radius} метров.", reply_markup=markup)
    else:
        response = f"Найденные места в радиусе {radius} метров:\n"
        for i, place in enumerate(places, 1):
            address = get_location_by_coordinates(place["lat"], place["lon"])
            response += (
                f'{i}. {place["name"]}\n'
                f'Адрес: г. {address["city"]}, ул. {address["street"]} {address["house_number"]}\n'
                f'Координаты: {place["lat"]}, {place["lon"]}\n'
                '— — — — —\n')
        bot.send_message(message.chat.id, response, reply_markup=markup)

# Запуск бота
if __name__ == "__main__":
    print("Бот запущен.")
    bot.infinity_polling()
