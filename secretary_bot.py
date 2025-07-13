
import telebot
from telebot import types
import requests
import os
from calendar_service import start_oauth_flow, complete_oauth_flow, create_calendar_event
from flask import Flask, request, session
import threading
import json  # Добавлен импорт для работы с JSON


# Инициализация Flask сервера для OAuth callback
app = Flask(__name__)
REDIRECT_URI = "http://localhost:5000/oauth2callback"
# Конфигурация Telegram бота
TOKEN = '7485538194:AAFFAPgQE1NZOsQ6wJ5V9GYeBXJ4AqhCeNU'
bot = telebot.TeleBot(TOKEN)

# Конфигурация Yandex GPT
id_ya = ""
key_ya = ""
# Хранилище состояний пользователей
user_states = {}

def run_flask_app():
    app.run(host='0.0.0.0', port=5000)

# Запускаем Flask в отдельном потоке
flask_thread = threading.Thread(target=run_flask_app)
flask_thread.daemon = True
flask_thread.start()

@app.route("/")
def home():
    return "Secretary Bot OAuth Server is running!"

@app.route("/oauth2callback")
def oauth2callback():
    code = request.args.get("code")
    state = request.args.get("state")
    
    print(f"[DEBUG] OAuth callback received - code: {code[:10]}..., state: {state}")
    
    if not code or not state:
        return "Ошибка: не передан code или state", 400
    
    try:
        # Разделяем state на chat_id и user_id
        parts = state.split('_')
        if len(parts) < 2:
            print(f"[ERROR] Invalid state format: {state}")
            return "Неверный формат state", 400
            
        chat_id, user_id = parts[0], parts[1]
        print(f"[DEBUG] Extracted chat_id: {chat_id}, user_id: {user_id}")
        
        user_id, creds = complete_oauth_flow(state, code)
        
        bot.send_message(chat_id, "✅ Авторизация в Google Calendar прошла успешно!")
        return "Авторизация прошла успешно! Вы можете закрыть эту вкладку."
    except Exception as e:
        print(f"[ERROR] OAuth callback error: {e}")
        # Пытаемся извлечь chat_id для отправки сообщения об ошибке
        chat_id = state.split('_')[0] if state and '_' in state else None
        if chat_id:
            try:
                bot.send_message(chat_id, f"❌ Ошибка авторизации: {str(e)}")
            except:
                pass  # Игнорируем ошибки отправки сообщения
        return f"Ошибка при авторизации: {e}", 500

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("👋 Поздороваться")
    markup.add(btn1)
    bot.send_message(message.chat.id, "👋 Привет! Я твой бот-секретарь!", reply_markup=markup)

@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get('step') == 'confirm_event')
def handle_confirmation(message):
    print(f"[DEBUG] handle_confirmation called with text: {message.text}")
    print(f"[DEBUG] user_states for chat_id {message.chat.id}: {user_states.get(message.chat.id)}")
    
    if message.text == '✅ Да, добавить':
        print(f"[DEBUG] Processing 'Да, добавить' for user {message.from_user.id}")
        try:
            event_data_str = user_states[message.chat.id]['event_data']
            print(f"[DEBUG] Event data string: {event_data_str}")
            event_data = json.loads(event_data_str)
            user_id = message.from_user.id
            print(f"[DEBUG] Parsed event_data: {event_data}")
            print(f"[DEBUG] user_id: {user_id}")
            
            # Проверяем, является ли event_data списком (несколько событий)
            if isinstance(event_data, list):
                for event in event_data:
                    print(f"[DEBUG] Creating calendar event for: {event}")
                    result = create_calendar_event(user_id, event)
                    print(f"[DEBUG] Calendar event result: {result}")
                    if "error" in result:
                        bot.send_message(message.chat.id, f"Ошибка при создании события: {result['error']}")
                    else:
                        event_link = result.get("htmlLink", "Ссылка не найдена")
                        bot.send_message(message.chat.id, f"Событие '{event.get('мероприятие', event.get('название', 'Без названия'))}' успешно создано!\n{event_link}")
            else:
                # Одно событие
                print(f"[DEBUG] Creating single calendar event: {event_data}")
                result = create_calendar_event(user_id, event_data)
                print(f"[DEBUG] Calendar event result: {result}")
                if "error" in result:
                    bot.send_message(message.chat.id, f"Ошибка при создании события: {result['error']}")
                else:
                                event_link = result.get("htmlLink", "Ссылка не найдена")
                                bot.send_message(message.chat.id, f"Событие успешно создано!\n{event_link}")
                                
                                # Показываем кнопку "Назад"
                                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                                btn_back = types.KeyboardButton('⬅️ Назад')
                                markup.add(btn_back)
                                bot.send_message(message.chat.id, "Что делаем дальше?", reply_markup=markup)
                    
        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON decode error: {e}")
            bot.send_message(message.chat.id, "Ошибка: неверный формат данных события")
        except Exception as e:
            print(f"[ERROR] Exception in handle_confirmation: {e}")
            bot.send_message(message.chat.id, f"Ошибка: {str(e)}")
        
    elif message.text == '❌ Нет, отменить':
        print(f"[DEBUG] Processing 'Нет, отменить' for user {message.from_user.id}")
        bot.send_message(message.chat.id, "Событие не было добавлено в календарь.")
        
        # Показываем кнопку "Назад"
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn_back = types.KeyboardButton('⬅️ Назад')
        markup.add(btn_back)
        bot.send_message(message.chat.id, "Что делаем дальше?", reply_markup=markup)
    
    # Очищаем состояние пользователя
    if message.chat.id in user_states:
        del user_states[message.chat.id]
        print(f"[DEBUG] Cleared user_states for chat_id {message.chat.id}")

@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    if message.text == '👋 Поздороваться':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton('Добавить мероприятие')
        btn2 = types.KeyboardButton('Мой календарь')
        btn3 = types.KeyboardButton('Авторизоваться в Google Calendar')
        markup.add(btn1, btn2, btn3)
        bot.send_message(message.chat.id, 'Выберите действие:', reply_markup=markup)

    elif message.text == 'Добавить мероприятие':
        msg = bot.send_message(message.chat.id, 'Отправьте мне текст с информацией о событии!')
        bot.register_next_step_handler(msg, process_event_description)

    elif message.text == 'Мой календарь':
        bot.send_message(message.chat.id, 'Вот ссылка на ваш Google Calendar: https://calendar.google.com')

    elif message.text == 'Авторизоваться в Google Calendar':
        start_auth(message)
        
    elif message.text == '⬅️ Назад':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton('Добавить мероприятие')
        btn2 = types.KeyboardButton('Мой календарь')
        btn3 = types.KeyboardButton('Авторизоваться в Google Calendar')
        markup.add(btn1, btn2, btn3)
        bot.send_message(message.chat.id, 'Выберите действие:', reply_markup=markup)

def start_auth(message):
    try:
        # Сохраняем chat_id и user_id в state для callback
        state = f"{message.chat.id}_{message.from_user.id}"
        auth_url, _ = start_oauth_flow(message.from_user.id, REDIRECT_URI, state)
        
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton("Авторизоваться", url=auth_url)
        markup.add(btn)
        
        bot.send_message(
            message.chat.id,
            "Для авторизации перейдите по ссылке:",
            reply_markup=markup
        )
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка при запуске авторизации: {str(e)}")

def process_event_description(message):
    try:
        event_text = message.text
        print(f"[DEBUG] Processing event description: {event_text}")
        structured_data = gpt(event_text)
        print(f"[DEBUG] GPT response: {structured_data}")
        
        # Пытаемся распарсить JSON для проверки его валидности
        try:
            json.loads(structured_data)
            print(f"[DEBUG] JSON is valid")
        except json.JSONDecodeError as e:
            print(f"[ERROR] Invalid JSON from GPT: {e}")
            bot.send_message(message.chat.id, "Не удалось корректно обработать информацию о событии. Пожалуйста, попробуйте еще раз.")
            return
        
        # Сохраняем данные события для пользователя
        user_states[message.chat.id] = {
            'event_data': structured_data,
            'step': 'confirm_event'
        }
        print(f"[DEBUG] Set user_states for chat_id {message.chat.id}: {user_states[message.chat.id]}")
        
        # Отправляем пользователю результат обработки для подтверждения
        bot.send_message(
            message.chat.id,
            f"Я распознал следующее событие:\n\n{structured_data}\n\nДобавить его в календарь?",
            reply_markup=create_confirmation_markup()
        )
        
    except Exception as e:
        print(f"[ERROR] Exception in process_event_description: {e}")
        bot.send_message(message.chat.id, f"Произошла ошибка при обработке: {str(e)}")

def create_confirmation_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton('✅ Да, добавить')
    btn2 = types.KeyboardButton('❌ Нет, отменить')
    markup.add(btn1, btn2)
    return markup

def gpt(text):
    prompt = {
        "modelUri": f"gpt://{id_ya}/yandexgpt",
        "completionOptions": {
            "stream": False,
            "temperature": 0.6,
            "maxTokens": "2000"
        },
        "messages": [
            {
                'role':'system',
                'text': '''
-Ты бот помощник-секретарь, который помогает создать напоминание в гугл-календаре по пересланному приглашению
-Твоя задача вытянуть из этого приглашения вытащить дату, название мероприятия, время проведения, описание и место проведения в формате json
-Если в сообщении несколько мероприятий на которые приглашён пользователь, то ты также составляешь несколько отдельных объектов в json файле, сторого соблюдая свзянанность: какому событию какие данные соответствуют и выдаёшь это одним результатом.
-Ты возвращаешь ТОЛЬКО json ответ
-Дату всегда возвращай в формате: dd.mm.yyyy
-Если год не указан в тексте, используй 2025 год
-Если в сообщении от пользователя не указана дата проведения мероприятия, но есть слова по типу: "Сегодня", "Завтра", "В следующую пятницу" и т.д. то в соответсвующем поле оставь: "Неявно указанная дата"
-Используй следующие ключи в JSON: "мероприятие" (название), "дата", "время", "описание", "место"
'''
            },
            {
                "role": "user",
                "text": text
            }
        ]
    }

    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Api-Key {key_ya}"
    }

    response = requests.post(url, headers=headers, json=prompt)
    if response.status_code != 200:
        raise Exception(f"Yandex GPT API error: {response.text}")
        
    result = response.json().get('result', {})
    if not result:
        raise Exception("Empty response from Yandex GPT")
        
    alternatives = result.get('alternatives', [])
    if not alternatives:
        raise Exception("No alternatives in response")
        
    response_text = alternatives[0].get('message', {}).get('text', '')
    if not response_text:
        raise Exception("Empty response text")

    # Очистка ответа от возможных обратных кавычек
    if response_text.startswith("```") and response_text.endswith("```"):
        response_text = response_text[3:-3].strip()
    elif response_text.startswith("```json") and response_text.endswith("```"):
        response_text = response_text[7:-3].strip()
        
    return response_text

if __name__ == '__main__':
    print("Бот запущен...")
    bot.polling(none_stop=True)