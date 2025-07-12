from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

import os
import pickle
import pytz
from datetime import datetime, timedelta
from typing import Dict

# ========== Настройки ==========
SCOPES = ["https://www.googleapis.com/auth/calendar.events"]
TIMEZONE = "Europe/Moscow"
CLIENT_SECRETS_FILE = "credentials.json"
TOKEN_DIR = "tokens"
TOKEN_FILE_TEMPLATE = os.path.join(TOKEN_DIR, "user_{user_id}.pickle")

# ========== Хранилище данных ==========
user_tokens = {}  # { user_id: { "credentials": Credentials } }
auth_flows = {}   # { state: Flow }

def get_calendar_service(user_id):
    """
    Возвращает Google Calendar API service для конкретного пользователя.
    Если токена нет или он истёк — пытается обновить или возвращает None.
    """
    if user_id in user_tokens:
        creds = user_tokens[user_id]["credentials"]
        if creds and creds.valid:
            return build("calendar", "v3", credentials=creds)
        elif creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                user_tokens[user_id]["credentials"] = creds
                save_user_token(user_id, creds)
                return build("calendar", "v3", credentials=creds)
            except Exception as e:
                print(f"[Ошибка] Не удалось обновить токен для пользователя {user_id}: {e}")
                del user_tokens[user_id]
                return None
    else:
        if load_user_token(user_id):
            return get_calendar_service(user_id)
    return None

def start_oauth_flow(user_id, redirect_uri: str):
    """
    Начинает OAuth flow для пользователя.
    Возвращает URL для авторизации и state.
    """
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=redirect_uri
    )
    auth_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    auth_flows[state] = flow
    return auth_url, state

def complete_oauth_flow(state: str, code: str):
    """
    Завершает OAuth flow по коду.
    Возвращает user_id (state) и Credentials.
    """
    flow = auth_flows.get(state)
    if not flow:
        raise Exception("OAuth flow не найден для указанного state")
    flow.fetch_token(code=code)
    creds = flow.credentials
    user_id = state
    user_tokens[user_id] = {"credentials": creds}
    save_user_token(user_id, creds)
    del auth_flows[state]
    return user_id, creds

def save_user_token(user_id, creds: Credentials):
    """
    Сохраняет токен пользователя на диск.
    """
    os.makedirs(TOKEN_DIR, exist_ok=True)
    token_path = TOKEN_FILE_TEMPLATE.format(user_id=user_id)
    with open(token_path, "wb") as token_file:
        pickle.dump(creds, token_file)

def load_user_token(user_id):
    """
    Загружает токен пользователя из файла, если он существует.
    """
    token_path = TOKEN_FILE_TEMPLATE.format(user_id=user_id)
    if os.path.exists(token_path):
        with open(token_path, "rb") as token_file:
            try:
                creds = pickle.load(token_file)
                if creds and creds.valid:
                    user_tokens[user_id] = {"credentials": creds}
                    return True
                elif creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                    user_tokens[user_id] = {"credentials": creds}
                    save_user_token(user_id, creds)
                    return True
            except Exception as e:
                print(f"[Ошибка] При загрузке токена: {e}")
    return False

def create_calendar_event(user_id, event_data: Dict):
    """
    Создаёт событие в календаре пользователя по его user_id.
    Принимает JSON с полями: название, дата, время, описание, место.
    """
    service = get_calendar_service(user_id)
    if not service:
        print(f"Не удалось получить доступ к календарю пользователя {user_id}")
        return {"error": "Пользователь не авторизован или токен недействителен"}

    event_name = event_data.get("название")
    description = event_data.get("описание", "")
    location = event_data.get("место", "")
    date_str = event_data.get("дата")
    time_str = event_data.get("время")

    if date_str == "Неявно указанная дата":
        print("Ошибка: не указана точная дата.")
        return {"error": "Дата не указана явно"}

    try:
        dt = datetime.strptime(f"{date_str} {time_str}", "%d.%m.%Y %H:%M")
        tz = pytz.timezone(TIMEZONE)
        start_datetime = tz.localize(dt)
        end_datetime = start_datetime + timedelta(hours=1)
    except Exception as e:
        print("Ошибка парсинга даты/времени:", e)
        return {"error": str(e)}

    event_body = {
        "summary": event_name,
        "location": location,
        "description": description,
        "start": {
            "dateTime": start_datetime.isoformat(),
            "timeZone": TIMEZONE,
        },
        "end": {
            "dateTime": end_datetime.isoformat(),
            "timeZone": TIMEZONE,
        },
    }

    try:
        event = service.events().insert(calendarId="primary", body=event_body).execute()
        print(f"Событие создано: {event.get('htmlLink')}")
        return event
    except Exception as e:
        print("Ошибка при создании события:", e)
        return {"error": str(e)}