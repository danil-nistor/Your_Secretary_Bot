# Secretary Bot - Бот-секретарь для Google Calendar

## Настройка Google OAuth

Для работы с Google Calendar API необходимо создать файл `credentials.json`.

### Шаги для получения credentials.json:

1. **Перейдите в Google Cloud Console:**
   - Откройте https://console.cloud.google.com/
   - Создайте новый проект или выберите существующий

2. **Включите Google Calendar API:**
   - В меню слева выберите "APIs & Services" → "Library"
   - Найдите "Google Calendar API" и включите его

3. **Создайте OAuth 2.0 credentials:**
   - Перейдите в "APIs & Services" → "Credentials"
   - Нажмите "Create Credentials" → "OAuth 2.0 Client IDs"
   - Выберите "Desktop application"
   - Дайте название (например, "Secretary Bot")
   - Нажмите "Create"

4. **Скачайте credentials.json:**
   - После создания клиента нажмите на него
   - Нажмите "Download JSON"
   - Сохраните файл как `credentials.json` в корневой папке проекта

### Структура файла credentials.json:
```json
{
  "installed": {
    "client_id": "ваш-client-id.apps.googleusercontent.com",
    "project_id": "ваш-project-id",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "ваш-client-secret",
    "redirect_uris": ["http://localhost"]
  }
}
```

## Установка зависимостей

```bash
# Активируйте виртуальную среду
.venv\Scripts\Activate.ps1

# Установите зависимости
pip install -r requirements.txt
```

## Запуск

### Тестовый режим:
```bash
python test_calendar.py
```

### Основной бот:
```bash
python secretary_bot.py
```

## Использование

1. Запустите бота
2. В Telegram найдите вашего бота
3. Отправьте команду `/start`
4. Выберите "Авторизоваться в Google Calendar"
5. Перейдите по ссылке и разрешите доступ
6. После авторизации можете добавлять события в календарь

## Структура проекта

- `secretary_bot.py` - основной Telegram бот
- `calendar_service.py` - сервис для работы с Google Calendar
- `test_gpt_calendar.py` - тестовый скрипт для проверки OAuth и записи события в календарь
- `credentials.json` - файл с OAuth credentials (нужно создать)
- `tokens/` - папка с сохраненными токенами пользователей 

## Предстоящие задачи:
- редактирование события + кнопки для каждого составляющего
- поправить определение даты
- отображать первые события (10 штук)
- возможность спросит: есть ли в N день событие
- возможность изменять уже существующее событие
- возможность удалять уже существующее событие
- если был отправлен текст с событием, то автоматически обрабатывать его и спрашивать, добавлять\редактировать\удалить
- настроить подключение к яндекс клауд
- возможность переключаться между аккаунтами в гугл
- обработка записей с картинкой
- обработка голосового сообщения
- обработка фотографии
- интегрирование на осетинский язык
- возможность подключения к яндекс аккаунту
- интегрирование работы с гугл календаря на яндекс календарь.

