import telebot
import json
import os
import requests
from telebot import types
from geopy.geocoders import Nominatim
from geopy.exc import GeopyError

API_2GIS_KEY = '' # токен 2Gis
API_TELEGRAM_TOKEN = '' # токен от BotFather

bot = telebot.TeleBot(API_TELEGRAM_TOKEN)

places_data_json = 'places_data.json'
database_json = 'user_requests.json'
channel_username = '@news_murziki'
users_json = 'users.json'

mcat = ["Рестораны", "Кафе", "Фастфуд", "Столовые", "Пекарни", "Магазины", "Технопарки", "Стартапы", "Гаджеты", "Магазины электроники", "Игровые клубы", "Магазины игр", "Киберспортивные арены", "Библиотеки", "Книжные магазины", "Книжные клубы", "Антикварные магазины", "Концертные залы", "Магазины музыкальных инструментов", "Музеи музыки", "Клубы", "Спортивные клубы", "Фитнес-центры", "Стадионы", "Магазины спортивных товаров", "Государственные музеи", "Музеи искусства", "Музеи науки", "Исторические музеи"]

def load_users():
    try:
        with open(users_json, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return []

def save_users(users):
    with open(users_json, 'w') as file:
        json.dump(users, file)

def add_user(user_id):
    users = load_users()
    if user_id not in users:
        users.append(user_id)
        save_users(users)

def notify_users(message):
    users = load_users()
    for user_id in users:
        try:
            bot.forward_message(chat_id=user_id, from_chat_id=message.chat.id, message_id=message.message_id)
        except Exception as e:
            print(f"Ошибка отправки пользователю {user_id}: {e}")

def load_data():
    try:
        with open(places_data_json, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_data(data):
    with open(places_data_json, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

def options_find(message):
    food_options = ["Рестораны", "Кафе", "Фастфуд", "Столовые", "Пекарни", "Магазины"]
    tech_options = ["Технопарки", "Стартапы", "Гаджеты", "Магазины электроники"]
    game_options = ["Игровые клубы", "Магазины игр", "Киберспортивные арены"]
    book_options = ["Библиотеки", "Книжные магазины", "Книжные клубы", "Антикварные магазины"]
    music_options = ["Концертные залы", "Магазины музыкальных инструментов", "Музеи музыки", "Клубы"]
    sport_options = ["Спортивные клубы", "Фитнес-центры", "Стадионы", "Магазины спортивных товаров"]
    museum_options = ["Государственные музеи", "Музеи искусства", "Музеи науки", "Исторические музеи"]
    
    if message.text == '🖥 Технологии':
        return tech_options
    elif message.text == '🎮 Игры':
        return game_options
    elif message.text == '📚 Книги':
        return book_options
    elif message.text == '🎵 Музыка':
        return music_options
    elif message.text == '🍕 Еда':
        return food_options
    elif message.text == '🏃 Спорт':
        return sport_options
    elif message.text == '🏛 Музеи':
        return museum_options

def categories_find(message):
    if message.text in ["Технопарки", "Стартапы", "Гаджеты", "Магазины электроники"]:
        return '🖥 Технологии'
    elif message.text in ["Игровые клубы", "Магазины игр", "Игровые консоли",  "Киберспортивные арены"]:
        return '🎮 Игры'
    elif message.text in ["Библиотеки", "Книжные магазины", "Книжные клубы", "Антикварные магазины"]:
        return '📚 Книги'
    elif message.text in ["Концертные залы", "Магазины музыкальных инструментов", "Музеи музыки", "Клубы"]:
        return '🎵 Музыка'
    elif message.text in ["Рестораны", "Кафе", "Фастфуд", "Столовые", "Пекарни", "Магазины"]:
        return '🍕 Еда'
    elif message.text in ["Спортивные клубы", "Фитнес-центры", "Стадионы", "Магазины спортивных товаров"]:
        return '🏃 Спорт'
    elif message.text in ["Государственные музеи", "Музеи искусства", "Музеи науки", "Исторические музеи"]:
        return '🏛 Музеи'

def get_location_by_coordinates(latitude: float, longitude: float) -> dict:
    try:
        geolocator = Nominatim(user_agent="location-finder")
        location = geolocator.reverse((latitude, longitude), language='ru')

        if location and location.raw:
            address = location.raw.get("address", {})
            street = address.get("road", "")
            house_number = address.get("house_number", "")
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

def send_feedback(message):
    developer_id = 5270288334
    feedback_text = message.text
    if message.text == 'Назад':
        start_message(message)
    else:
        try:
            bot.send_message(developer_id, f'Новый отзыв от пользователя {message.from_user.id}:\n{feedback_text}')
            bot.send_message(message.chat.id, 'Спасибо за Ваш отзыв! Он был отправлен разработчику.')
        except Exception as e:
            bot.send_message(message.chat.id, f'Произошла ошибка при отправке отзыва: {e}')
    start_message(message)

def menu_g_message(message):
    data = load_data()
    data_users = load_users()
    user_id = str(message.from_user.id)

    if user_id not in data_users:
        add_user(user_id)
    
    if user_id in data:
        del data[user_id]
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    find_places_button = types.KeyboardButton('🔍 Найти места')
    settings_button = types.KeyboardButton('⚙️ Настройки')
    help_button = types.KeyboardButton('📨 Помощь')
    feedback_button = types.KeyboardButton('☎️ Обратная связь')
    markup.add(find_places_button)
    markup.add(settings_button)
    markup.add(help_button, feedback_button)

    bot.send_message(message.chat.id, 'Главное меню', reply_markup=markup)

@bot.channel_post_handler(func=lambda message: True)
def channel_message_handler(message):
    if message.chat.username == channel_username.lstrip("@"):
        notify_users(message)
        
@bot.message_handler(commands=['start'])
def start_message(message):
    data_users = load_users()
    user_id = str(message.from_user.id)

    if user_id not in data_users:
        add_user(user_id)
        
    menu_message(message)

@bot.message_handler(func=lambda message: message.text == 'Назад')
def go_back(message):
    menu_message(message)

@bot.message_handler(func=lambda message: message.text == '📖 Меню')
def menu_message(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    find_places_button = types.KeyboardButton('🔍 Найти места')
    settings_button = types.KeyboardButton('⚙️ Настройки')
    help_button = types.KeyboardButton('📨 Помощь')
    feedback_button = types.KeyboardButton('☎️ Обратная связь')
    markup.add(find_places_button)
    markup.add(settings_button)
    markup.add(help_button, feedback_button)

    bot.send_message(message.chat.id, 'Приветствую!\n'
                                      'Это городской бот, который поможет найти интересные места рядом с Вами.\n'
                                      'Для начала работы, Вы можете использовать кнопки ниже!', reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == '⚙️ Настройки')
def settings_handler(message):
    bot.send_message(message.chat.id, 'Здесь будут Ваши последние запросы:\n'
                                      '---')

@bot.message_handler(func=lambda message: message.text == '☎️ Обратная связь')
def feedback_handler(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    back_button = types.KeyboardButton('Назад')
    markup.add(back_button)

    bot.send_message(message.chat.id, 'Напишите свой вопрос или предложение прямо сюда!', reply_markup=markup)
    bot.register_next_step_handler(message, send_feedback)

@bot.message_handler(func=lambda message: message.text == '📨 Помощь')
def show_help(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    back_button = types.KeyboardButton('Назад')
    markup.add(back_button)

    help_text = (
        "Справка по работе с ботом:\n"
        "1. Используйте кнопку 'Найти места', чтобы выбрать интересы и найти ближайшие места.\n"
        "2. Отправьте своё местоположение, чтобы бот нашёл интересные места поблизости.\n"
        "3. Если возникли проблемы, попробуйте снова или напишите разработчику.\n"
        "\nМы всегда рады помочь!")
    bot.send_message(message.chat.id, help_text, reply_markup=markup)

@bot.message_handler(func=lambda message: message.text in ['🔍 Найти места', '✨ Попробовать ещё раз'])
def your_places_to_find(message):
    data = load_data()
    user_id = str(message.from_user.id)

    if user_id in data:
        del data[user_id]
    
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    interests = ["🖥 Технологии", "🎮 Игры", "📚 Книги", "🎵 Музыка", "🍕 Еда", "🏃 Спорт", "🏛 Музеи"]
    buttons = [types.KeyboardButton(interest) for interest in interests]
    markup.add(*buttons)
    bot.send_message(message.chat.id, "Выбери свой интерес:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text in ["🖥 Технологии", "🎮 Игры", "📚 Книги", "🎵 Музыка", "🍕 Еда", "🏃 Спорт", "🏛 Музеи"])
def handle_interest_for(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    
    options = options_find(message)

    buttons = [types.KeyboardButton(option) for option in options]
    markup.add(*buttons)

    bot.send_message(message.chat.id, 'Выберите подкатегорию:', reply_markup=markup)

@bot.message_handler(func=lambda message: message.text in mcat)
def handle_categories(message):
    category = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    location_button = types.KeyboardButton('📍 Отправить местоположение', request_location=True)
    markup.add(location_button)

    categories = categories_find(message)

    bot.send_message(message.chat.id, f'Вы выбрали интерес: {categories}/{category}. Теперь отправьте сюда Ваше местоположение, чтобы я мог найти ближайшие места.', reply_markup=markup)
    bot.register_next_step_handler(message, lambda msg: handle_search(msg, message.text))

@bot.message_handler(func=lambda message: message.text == '🗺️ Показать в мини-приложении')
def pre_mini(message):
    data = load_data()
    user_id = str(message.from_user.id)
    
    if user_id not in data:
        data[user_id] = []
    
    try:
        markup = types.InlineKeyboardMarkup(row_width=2)
        buttons = []
        for i in range(len(data[user_id])):
            web_app_info = types.WebAppInfo(url=data[user_id][i])
            buttons.append(types.InlineKeyboardButton(text='Перейти', web_app=web_app_info))
        markup.add(*buttons)

        bot.send_message(message.chat.id, text='Ниже к каждому месту, прикреплена навигация до этого места', reply_markup=markup, disable_web_page_preview=True)
        del data[user_id]
        save_data(data)
        menu_g_message(message)
    except Exception:
        bot.send_message(message.chat.id, text='Не получилось отправить ссылки(')
        menu_g_message(message)

def handle_search(message, query):
    data = load_data()
    user_id = str(message.from_user.id)
    lat = None
    lon = None
    places = None

    if user_id not in data:
        data[user_id] = []
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    app_start_button = types.KeyboardButton('🗺️ Показать в мини-приложении')
    restart_button = types.KeyboardButton('✨ Попробовать ещё раз')
    menu_button = types.KeyboardButton('📖 Меню')
    markup.add(app_start_button)
    markup.add(restart_button)
    markup.add(menu_button)
    
    radius = 1000

    if message.location is not None:
        lat = message.location.latitude
        lon = message.location.longitude

    bot.send_message(message.chat.id, f"Ищу места по теме: '{query}' в радиусе {radius} метров...")
    try:
        places = find_places_in_2gis(query, lat, lon, radius)
    except Exception:
        bot.send_message(message.chat.id, f"Ничего не найдено по запросу '{query}' в радиусе {radius} метров.", reply_markup=markup)

    if not places:
        bot.send_message(message.chat.id, f"Ничего не найдено по запросу '{query}' в радиусе {radius} метров.", reply_markup=markup)
    else:
        response = f"Найденные места в радиусе {radius} метров:\n"
        for i, place in enumerate(places, 1):
            address = get_location_by_coordinates(place["lat"], place["lon"])
            yandex_maps_url = f'https://yandex.ru/maps/?rtext={lat},{lon}~{place["lat"]},{place["lon"]}&rtt=auto'
            response += (
                f'{i}. {place["name"]}\n'
                f'Адрес: г. {address["city"]}, ул. {address["street"]} {address["house_number"]}\n'
                f'Координаты: {place["lat"]}, {place["lon"]}\n'
                f'Открыть в Яндекс.Картах: {yandex_maps_url}\n'
                '— — — — — — —\n')
            data[user_id].append(yandex_maps_url)
            save_data(data)
        bot.send_message(message.chat.id, f'{response}\n'
                                          f'Для показа навигации в мини-приложении, нажмите кнопку ниже...', reply_markup=markup, disable_web_page_preview=True)

# Запуск бота
if __name__ == "__main__":
    print("Бот запущен.")
    bot.infinity_polling()
