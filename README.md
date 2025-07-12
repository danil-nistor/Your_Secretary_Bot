# 📅 Telegram Bot: Автоматическое создание событий в Google Calendar

Этот проект реализует Telegram-бота, который позволяет пользователю отправлять текстовое сообщение с описанием события (например: «Завтра в 15:00 встреча с командой»), автоматически извлекает из него данные с помощью Yandex GPT и создаёт напоминание в Google Calendar.

## 🧩 Возможности

- Получение текстового сообщения от пользователя.
- Извлечение даты, времени, названия и описания события с помощью Yandex GPT.
- Создание события в Google Calendar.
- Поддержка OAuth2 авторизации для нескольких пользователей (готов к масштабированию).
- Локальное тестирование без выкладывания на сервер.

---

## 📁 Структура проекта

```
project_root/
├── bot.py                  # Основной Telegram-бот
├── calendar_service.py     # Работа с Google Calendar API
├── gpt.py                  # Интеграция с Yandex GPT
├── config.py               # Конфигурационные параметры
├── credentials.json        # Ключи Google Cloud Console
├── .env                    # Переменные окружения
├── tokens/                 # Сохранённые токены пользователей
├── requirements.txt        # Зависимости Python
└── README.md               # Документация
```

---

## 🔧 Установка и настройка

### 1. Получи токен Telegram бота

- Напиши [@BotFather](https://t.me/BotFather) в Telegram.
- Создай нового бота и сохрани токен.

### 2. Настрой Google Calendar API

1. Перейди в [Google Cloud Console](https://console.cloud.google.com/).
2. Создай новый проект или используй существующий.
3. Включи **Google Calendar API**.
4. Создай **OAuth Client ID** типа "Other".
5. Скачай `credentials.json` и положи его в корень проекта.

### 3. Установи зависимости

```bash
pip install -r requirements.txt
```

### 4. Настрой переменные окружения

Создай файл `.env`:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
```

---

## 🚀 Как запустить

### Для тестирования локально:

#### Вариант 1: Webhook + ngrok (рекомендуется для продвинутых)

1. Запусти Flask-сервер:
   ```bash
   python bot.py
   ```

2. В другом терминале запусти ngrok:
   ```bash
   ngrok http 8000
   ```

3. Установи webhook:
   ```bash
   curl -F "url=https://abcd1234.ngrok.io/webhook" https://api.telegram.org/bot<your_token>/setWebhook
   ```

#### Вариант 2: Polling (просто и быстро)

```bash
python bot.py
```

---

## 🧪 Тестирование работы с Google Calendar

Можно запустить тестовый скрипт:

```bash
python test_calendar.py
```

Он:
- Проведёт OAuth один раз.
- Создаст тестовое событие.
- Проверит работу модуля `calendar_service.py`.

---

## 👥 Как работает система с несколькими пользователями

- Каждый пользователь проходит OAuth через Telegram.
- Авторизационный код сохраняется в `tokens/user_{id}.pickle`.
- Все дальнейшие действия с календарём происходят под этим аккаунтом.

> ✅ MVP поддерживает мультипользовательский режим, но легко адаптируется под одного пользователя.

---

## 📦 Пример использования `calendar_service.py`

```python
from calendar_service import get_calendar_service, create_calendar_event

user_id = 123456789  # Telegram ID пользователя

# Получаем доступ к календарю
service = get_calendar_service(user_id)

# Если доступ есть — создаём событие
if service:
    event_data = {
        "название": "Переговоры",
        "дата": "05.04.2025",
        "время": "15:00",
        "описание": "Обсуждение проекта",
        "место": "Офис"
    }
    result = create_calendar_event(user_id, event_data)
    print("Событие создано:", result.get('htmlLink'))
else:
    print("Пользователь не авторизован.")
```

---

## 🤝 Для команды: как использовать `calendar_service.py`

Твой коллега может использовать `calendar_service.py` следующим образом:

1. Получить текст сообщения от пользователя.
2. Передать его в функцию `extract_event_info()` (в `gpt.py`) для получения `event_data`.
3. Вызвать `create_calendar_event(user_id, event_data)`.

Пример:

```python
from gpt import extract_event_info
from calendar_service import create_calendar_event

def handle_message(update, context):
    user_id = update.message.from_user.id
    message_text = update.message.text

    event_data = extract_event_info(message_text)
    result = create_calendar_event(user_id, event_data)

    if "error" in result:
        update.message.reply_text(f"Ошибка: {result['error']}")
    else:
        update.message.reply_text("Событие успешно создано!")
```

---

## 📌 Полезные ссылки

- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Google Calendar API Docs](https://developers.google.com/calendar)
- [Yandex GPT](https://cloud.yandex.ru/services/yandex_gpt)
- [ngrok — проброс портов](https://ngrok.com/)

---

## 🛠️ Roadmap / Что можно добавить дальше

- Поддержка повторяющихся событий.
- Распознавание естественных выражений («через 2 дня», «завтра», «в пятницу»).
- Интерактивный диалог с пользователем при недостающих данных.
- Хранение истории событий.
- Docker-образ для простого развёртывания.

---

## ❤️ Благодарности

Спасибо за использование!  
Если тебе помог этот шаблон — звёздочка на GitHub будет отличным подарком 🌟

--- 

Хочешь, я подготовлю этот README в виде файла, чтобы ты мог сразу загрузить его в свой репозиторий?
