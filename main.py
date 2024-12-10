import telebot
import requests
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# Данные бота
YANDEX_API_KEY = 'ac3b9335-a8aa-4b72-8993-81253dfdc199'
TOKEN = '7345327846:AAF2HRPVwVnKF5hpHo3u4zmDwSlARQDPRLk'
bot = telebot.TeleBot(TOKEN)

# Данные пользователя
user_interests = {}
user_location = {}
user_state = {}

# ID администратора
ADMIN_ID = '6118296596'

# Состояния для отслеживания
STATE_INTEREST = 'interest'
STATE_LOCATION = 'location'
STATE_MAIN = 'main'
STATE_FEEDBACK = 'feedback'

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, 'Привет! Это городской бот. Я помогу тебе найти интересные места поблизости.')
    user_state[message.chat.id] = STATE_MAIN
    send_main_menu(message)

def send_main_menu(message):
    """Главное меню с кнопками"""
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(KeyboardButton("🗺️ Найти места"), KeyboardButton("❓ Помощь"), KeyboardButton("💬 Оставить отзыв"))
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "❓ Помощь")
def send_help(message):
    """Отправка инструкции по использованию бота"""
    help_text = (
        "Привет! Я помогу тебе найти интересные места поблизости.\n\n"
        "Вот как ты можешь использовать бота:\n"
        "1. Нажми на кнопку '🗺️ Найти места' чтобы начать искать интересные места.\n"
        "2. Выбери свой интерес из предложенных вариантов (например, 'Еда', 'Спорт', 'Музеи').\n"
        "3. Отправь своё местоположение, чтобы бот мог найти ближайшие места.\n\n"
        "Если нужно вернуться назад, нажми '⬅️ Назад'.\n"
        "Для любых вопросов, ты всегда можешь вернуться сюда, нажав '❓ Помощь'."
    )
    bot.send_message(message.chat.id, help_text)
    send_main_menu(message)

@bot.message_handler(func=lambda message: message.text == "💬 Оставить отзыв")
def handle_feedback(message):
    """Запрос отзыва от пользователя"""
    user_state[message.chat.id] = STATE_FEEDBACK
    bot.send_message(message.chat.id, "Напишите ваш отзыв или сообщение о проблеме. Мы обязательно рассмотрим его.")

@bot.message_handler(func=lambda message: user_state.get(message.chat.id) == STATE_FEEDBACK)
def receive_feedback(message):
    """Получение отзыва и отправка его администратору"""
    feedback = message.text

    bot.send_message(ADMIN_ID, f"Новый отзыв от пользователя {message.chat.id}:\n{feedback}")
    bot.send_message(message.chat.id, "Спасибо за ваш отзыв! Мы обязательно его рассмотрим.")
    send_main_menu(message)

@bot.message_handler(func=lambda message: message.text == "🗺️ Найти места")
def start_find_places(message):
    """Начать процесс поиска мест"""
    user_state[message.chat.id] = STATE_INTEREST
    send_interest_request(message)

def send_interest_request(message):
    """Отправка пользователю кнопок с интересами для выбора"""
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    interests = ["🖥 Технологии", "🎮 Игры", "📚 Книги", "🎵 Музыка", "🍕 Еда", "🏃 Спорт", "🏛 Музеи"]
    buttons = [KeyboardButton(interest) for interest in interests]
    markup.add(*buttons, KeyboardButton("⬅️ Назад"))
    bot.send_message(message.chat.id, "Выбери свой интерес:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text in ["🖥 Технологии", "🎮 Игры", "📚 Книги", "🎵 Музыка", "🍕 Еда", "🏃 Спорт", "🏛 Музеи"])
def handle_interest(message):
    """Обработка выбора интереса и запрос местоположения"""
    user_interests[message.chat.id] = message.text
    bot.reply_to(message, f"Ты выбрал интерес: {message.text}. Теперь отправь мне своё местоположение, чтобы я мог найти ближайшие места.")
    user_state[message.chat.id] = STATE_LOCATION
    send_location_request(message)

@bot.message_handler(func=lambda message: message.text == "⬅️ Назад")
def handle_back(message):
    """Обработка нажатия кнопки Назад"""
    state = user_state.get(message.chat.id, STATE_MAIN)

    if state == STATE_INTEREST:
        send_main_menu(message)
    elif state == STATE_LOCATION:
        send_interest_request(message)
    else:
        send_main_menu(message)

def send_location_request(message):
    """Отправка запроса на получение местоположения"""
    markup = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    location_button = KeyboardButton("📍 Отправить местоположение", request_location=True)
    back_button = KeyboardButton("⬅️ Назад")
    markup.add(location_button, back_button)
    bot.send_message(message.chat.id, "Пожалуйста, отправь своё местоположение:", reply_markup=markup)

@bot.message_handler(content_types=['location'])
def handle_location(message):
    """Обработка получения местоположения и поиск ближайших мест"""
    if message.location:
        latitude, longitude = message.location.latitude, message.location.longitude
        user_location[message.chat.id] = (latitude, longitude)

        interest = user_interests.get(message.chat.id)
        if interest:
            places = search_nearby_places(YANDEX_API_KEY, latitude, longitude, interest)
            send_places(message.chat.id, places)
        else:
            bot.send_message(message.chat.id, "Пожалуйста, выбери свой интерес сначала.")
    else:
        bot.send_message(message.chat.id, "Не удалось получить местоположение. Попробуй снова.")

def send_places(chat_id, places):
    """Отправка списка мест пользователю"""
    if places:
        for place in places:
            bot.send_message(chat_id, place)
    else:
        bot.send_message(chat_id, "Не удалось найти подходящие места рядом.")

def get_nearby_places(query, latitude, longitude, radius=20.0):
    """Поиск ближайших мест с использованием Яндекс.Карт API"""
    url = "https://search-maps.yandex.ru/v1/"
    params = {
        "apikey": YANDEX_API_KEY,
        "text": query,
        "ll": f"{longitude},{latitude}",
        "spn": f"{radius},{radius}",
        "type": "biz",
        "lang": "ru_RU",
        "results": 5
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        if 'features' in data:
            places = []
            for feature in data["features"]:
                place = feature["properties"]
                name = place["name"]
                address = place.get("description", "Не указано")
                coordinates = feature["geometry"]["coordinates"]
                places.append(f"Место: {name}\nАдрес: {address}\nКоординаты: {coordinates}")
            return places
        else:
            return []
    else:
        print(f"Ошибка запроса: {response.status_code}, {response.text}")
        return []

def search_nearby_places(api_key, latitude, longitude, query):
    """Поиск мест по интересу пользователя"""
    return get_nearby_places(query, latitude, longitude)

if __name__ == "__main__":
    print("Бот запущен.")
    bot.infinity_polling()
