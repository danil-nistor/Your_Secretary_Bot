# Быстрый старт

## 1. Установка зависимостей
```bash
pip install -r requirements.txt
```

## 2. Настройка API ключей

### Yandex GPT (обязательно)
В файле `gpt.py` замените:
```python
id_ya = "ВАШ_FOLDER_ID"  # Folder ID из Yandex Cloud
key_ya = "ВАШ_API_КЛЮЧ"  # API-ключ из Yandex Cloud
```

### Google Calendar (для полного тестирования)
1. Создайте проект в Google Cloud Console
2. Включите Google Calendar API
3. Создайте OAuth 2.0 credentials
4. Скачайте `credentials.json` в корневую папку

## 3. Тестирование

### Только GPT (без календаря)
```bash
python test_gpt_only.py
```

### Полный тест с календарем
```bash
python test_gpt_calendar.py
```
Затем откройте http://localhost:5000

## 4. Структура данных

GPT возвращает:
```json
{
  "мероприятие": "Название события",
  "дата": "dd.mm.yyyy", 
  "время": "HH:MM",
  "описание": "Описание",
  "место": "Место проведения"
}
```

Календарь ожидает:
```json
{
  "start": {
    "dateTime": "2025-10-15T10:00:00+03:00",
    "timeZone": "Europe/Moscow"
  },
  "end": {
    "dateTime": "2025-10-15T11:00:00+03:00",
    "timeZone": "Europe/Moscow"
  }
}
```

Функция `normalize_event()` автоматически преобразует формат. 
