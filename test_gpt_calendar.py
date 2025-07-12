from flask import Flask, request, redirect, session
import json
from calendar_service import start_oauth_flow, complete_oauth_flow, create_calendar_event, load_user_token
from gpt import gpt, normalize_event

app = Flask(__name__)
app.secret_key = "your_secret_key_123456"  # Для работы сессий, замените на свой

# ==== Настройки ====
TEST_USER_ID = "123456789"  # ← Можно убрать, если не нужен
REDIRECT_URI = "http://localhost:5000/oauth2callback"

test_message = """
Привет! У меня 19.07.2025 в 15:00 встреча с командой. Нужно обсудить план на месяц. 
Место проведения: офис, конференц-зал №3. Еще есть идея провести 21.07.2025 мини-хакотон в 13.00 и для большего удобвства в пройжёт онлайн 
"""

@app.route("/")
def index():
    return """
    <h2>Добро пожаловать!</h2>
    <ul>
      <li><a href="/start">/start</a> — начать авторизацию через Google</li>
      <li><a href="/process">/process</a> — обработать сообщение через GPT и создать событие</li>
    </ul>
    """

@app.route("/start")
def start_auth():
    print("Запуск OAuth потока...")
    try:
        auth_url, state = start_oauth_flow(TEST_USER_ID, REDIRECT_URI)
        print(f"\nПерейдите по ссылке: {auth_url}")
        return redirect(auth_url)
    except Exception as e:
        print(f"[ERROR] {e}")
        return f"Ошибка: {e}"

@app.route("/oauth2callback")
def oauth2callback():
    code = request.args.get("code")
    state = request.args.get("state")

    if not code or not state:
        return "Не передан 'code' или 'state'", 400

    print("\n[INFO] Получен код авторизации.")
    try:
        user_id, creds = complete_oauth_flow(state, code)
        session['user_id'] = user_id  # Сохраняем user_id в сессию
        print(f"[SUCCESS] Авторизация успешна для пользователя {user_id}")
        return f"""
        <h2>Авторизация прошла успешно!</h2>
        <p>Теперь перейдите по ссылке ниже, чтобы обработать сообщение:</p>
        <a href="/process">/process</a>
        """
    except Exception as e:
        print("[ERROR]", e)
        return f"Ошибка при авторизации: {e}", 500

@app.route("/process")
def process_message():
    user_id = session.get('user_id')
    if not user_id:
        return "<h2>Ошибка:</h2><p>Сначала авторизуйтесь через <a href='/start'>/start</a></p>"

    print("=== Шаг 1: Извлечение данных через Yandex GPT ===")

    raw_result = gpt(test_message)

    print("\nОтвет от GPT:")
    print(raw_result)  # Выведем сырой ответ для отладки

    if isinstance(raw_result, dict) and 'error' in raw_result:
        print("Ошибка при вызове GPT:", raw_result['error'])
        return f"<h2>Ошибка при вызове GPT:</h2><p>{raw_result['error']}</p>"

    print("\n=== Шаг 2: Преобразование формата данных ===")

    normalized_events = []

    if isinstance(raw_result, dict):
        normalized_events.append(normalize_event(raw_result))
    elif isinstance(raw_result, list):
        for event_data in raw_result:
            normalized_events.append(normalize_event(event_data))
    else:
        print("Неожиданный формат ответа от GPT.")
        return "<h2>Ошибка:</h2><p>Неожиданный формат ответа от GPT.</p>"

    print("\nПреобразованные данные для Calendar API:")
    print(json.dumps(normalized_events, indent=2, ensure_ascii=False))

    print("\n=== Шаг 3: Создание события(ий) в календаре ===")

    results = []
    for event_data in normalized_events:
        result = create_calendar_event(user_id, event_data)
        results.append(result)

        if "error" in result:
            print(f"Не удалось создать событие '{event_data.get('название')}': {result['error']}")
        else:
            print(f"Событие '{event_data.get('название')}' успешно создано!")

    output = "<h2>Результаты:</h2><ul>"
    has_success = False
    has_error = False

    for res in results:
        name = res.get("summary", "Без названия")
        if "htmlLink" in res:
            has_success = True
            output += f"<li>✅ <a href='{res['htmlLink']}' target='_blank'>{name}</a></li>"
        elif "error" in res:
            has_error = True
            output += f"<li>❌ {name}: {res['error']}</li>"

    output += "</ul>"

    if has_success:
        output += "<p><strong>🎉 События успешно созданы в Google Calendar!</strong></p>"
    if has_error:
        output += "<p><strong>⚠️ Некоторые события не удалось создать.</strong></p>"

    return output

if __name__ == "__main__":
    print("Запуск локального сервера для тестирования Google Calendar API...")
    print("Откройте http://localhost:5000 в браузере")
    app.run(host="localhost", port=5000, debug=True)