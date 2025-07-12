import requests
import json
import re

# Замените на свои значения
id_ya = "b1ghnehmnn3n3dvbqi90"  # Folder ID
key_ya = "AQVNz9XUQGq4KhejXKZ-8PLoDVwLZrPGARRazGnK"  # API-ключ

def normalize_event(event_data):
    """
    Приводит поля к нужному формату
    Поддерживает как прямые ключи, так и вложенную структуру event
    """
    # Если данные вложены в event, извлекаем их
    if isinstance(event_data, dict) and 'event' in event_data:
        event_data = event_data['event']
    
    return {
        "название": event_data.get("мероприятие") or event_data.get("event_name") or event_data.get("title") or event_data.get("name") or "Без названия",
        "дата": event_data.get("дата") or event_data.get("date"),
        "время": event_data.get("время") or event_data.get("time"),
        "описание": event_data.get("описание") or event_data.get("description", ""),
        "место": event_data.get("место") or event_data.get("location") or event_data.get("place", "")
    }

def clean_markdown_json(content: str) -> str:
    """
    Очищает JSON от Markdown обрамления
    Поддерживает различные форматы: ```json, ```, ```, и т.д.
    """
    # Убираем начальные пробелы и переносы строк
    content = content.strip()
    
    # Паттерн для поиска JSON в markdown блоках
    # Поддерживает: ```json, ```, ```, и другие варианты
    markdown_pattern = r'^```(?:json)?\s*\n?(.*?)\n?```$'
    
    # Пытаемся найти JSON в markdown блоке
    match = re.search(markdown_pattern, content, re.DOTALL)
    if match:
        return match.group(1).strip()
    
    # Если markdown блок не найден, возвращаем как есть
    return content

def gpt(text: str):
    """
    Отправляет текст в Yandex GPT и возвращает структурированные данные о событиях
    Возвращает:
    - dict: если одно событие
    - list: если несколько событий
    - dict с ключом "error": если произошла ошибка
    """
    prompt = {
        "modelUri": f"gpt://{id_ya}/yandexgpt",
        "completionOptions": {
            "stream": False,
            "temperature": 0.6,
            "maxTokens": "2000"
        },
        "messages": [
            {
                "role": "system",
                "text": '''-Ты бот помощник-секретарь, который помогает создать напоминание в гугл-календаре по пересланному приглашению
-Твоя задача вытянуть из этого приглашения дату, название мероприятия, время проведения, описание и место проведения в формате json
-Если в сообщении несколько мероприятий на которые приглашён пользователь, то ты также составляешь несколько отдельных объектов в json файле, строго соблюдая связь: какому событию какие данные соответствуют и выдаёшь это одним результатом.
-Ты возвращаешь ТОЛЬКО json ответ
-Дату всегда возвращай в формате: dd.mm.yyyy
-Если в сообщении от пользователя не указана дата проведения мероприятия, но есть слова по типу: "Сегодня", "Завтра", "В следующую пятницу" и т.д., то в соответсвующем поле оставь: "Неявно указанная дата"
-Используй русские ключи: мероприятие, дата, время, описание, место'''
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

    try:
        response = requests.post(url, headers=headers, json=prompt)

        if response.status_code != 200:
            print("Ошибка HTTP:", response.status_code)
            print(response.text)
            return {"error": f"HTTP {response.status_code}: {response.text}"}

        result = response.json().get('result')
        if not result:
            print("Пустой ответ от Yandex GPT")
            return {"error": "Пустой ответ от GPT"}

        content = result['alternatives'][0]['message']['text'].strip()

        print("Сырой ответ от GPT:")
        print(repr(content))  # Используем repr() чтобы видеть точное содержание

        # Очищаем от Markdown обрамления
        cleaned_content = clean_markdown_json(content)
        
        print("Очищенный контент:")
        print(repr(cleaned_content))

        # Парсим JSON
        parsed = json.loads(cleaned_content)

        # Возвращаем исходный формат от GPT (dict или list)
        return parsed

    except json.JSONDecodeError as e:
        print("Не удалось распарсить JSON:")
        print("Оригинальный контент:", repr(content))
        print("Очищенный контент:", repr(cleaned_content))
        return {"error": f"Ошибка парсинга JSON: {e}"}
    except KeyError as e:
        print("Ключ отсутствует в ответе GPT:", e)
        return {"error": f"Ответ GPT не содержит нужного ключа: {e}"}
    except Exception as e:
        print("Непредвиденная ошибка:", e)
        return {"error": f"Ошибка: {e}"}