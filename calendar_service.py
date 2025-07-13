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
CLIENT_SECRETS_FILE = "" # Здесь нужно ввести название файла содержащий Client secret
TOKEN_DIR = "tokens"
TOKEN_FILE_TEMPLATE = os.path.join(TOKEN_DIR, "user_{user_id}.pickle")

# ========== Хранилище данных ==========
user_tokens = {}  # { user_id: { "credentials": Credentials } }
auth_flows = {}   # { state: Flow }

# Глобальный словарь для хранения OAuth flows между потоками
import threading
import pickle
import tempfile
import os
_flows_lock = threading.Lock()
_flows = {}
_FLOWS_FILE = os.path.join(tempfile.gettempdir(), "oauth_flows.pickle")

def get_calendar_service(user_id: int):
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


def _save_flows():
    """Сохраняет flows в файл"""
    try:
        with open(_FLOWS_FILE, 'wb') as f:
            pickle.dump(_flows, f)
    except Exception as e:
        print(f"[ERROR] Failed to save flows: {e}")

def _load_flows():
    """Загружает flows из файла"""
    try:
        if os.path.exists(_FLOWS_FILE):
            with open(_FLOWS_FILE, 'rb') as f:
                return pickle.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to load flows: {e}")
    return {}

def start_oauth_flow(user_id: int, redirect_uri: str, custom_state: str = None):
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=redirect_uri
    )
    auth_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        state=custom_state
    )
    
    # Сохраняем flow в потокобезопасном хранилище
    with _flows_lock:
        _flows[state] = flow
        print(f"[DEBUG] OAuth flow started with state: {state}")
        print(f"[DEBUG] Available flows: {list(_flows.keys())}")
        _save_flows()
    
    return auth_url, state


def complete_oauth_flow(state: str, code: str):
    print(f"[DEBUG] Completing OAuth flow for state: {state}")
    
    # Проверяем, есть ли уже токен для этого пользователя
    if '_' in state:
        user_id = state.split('_')[1]
    else:
        user_id = state
        
    if user_id in user_tokens:
        print(f"[INFO] Токен для пользователя {user_id} уже существует")
        return user_id, user_tokens[user_id]["credentials"]
    
    # Создаем новый flow для завершения OAuth
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri="http://localhost:5000/oauth2callback"
    )
    
    try:
        flow.fetch_token(code=code)
        creds = flow.credentials

        # Сохраняем в память и на диск
        user_tokens[user_id] = {"credentials": creds}
        save_user_token(user_id, creds)

        return user_id, creds
    except Exception as e:
        print(f"[ERROR] Failed to complete OAuth flow: {e}")
        raise Exception(f"Ошибка при завершении OAuth: {e}")


def save_user_token(user_id: int, creds: Credentials):
    os.makedirs(TOKEN_DIR, exist_ok=True)
    token_path = TOKEN_FILE_TEMPLATE.format(user_id=user_id)
    with open(token_path, "wb") as token_file:
        pickle.dump(creds, token_file)


def load_user_token(user_id: int):
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


def create_calendar_event(user_id: int, event_data: Dict):
    service = get_calendar_service(user_id)
    if not service:
        return {"error": "Пользователь не авторизован или токен недействителен"}

    event_name = event_data.get("мероприятие") or event_data.get("название") or event_data.get("event_name")
    description = event_data.get("описание", "") or event_data.get("description", "")
    location = event_data.get("место", "") or event_data.get("location", "")
    date_str = event_data.get("дата") or event_data.get("date")
    time_str = event_data.get("время") or event_data.get("time")

    # Проверяем наличие даты
    if not date_str:
        return {"error": "Дата не указана"}
    
    if date_str == "Неявно указанная дата":
        return {"error": "Дата не указана явно"}

    # Проверяем наличие времени
    if not time_str:
        return {"error": "Время не указано"}

    # Обработка даты
    try:
        # Разбираем дату
        date_parts = date_str.split('.')
        if len(date_parts) != 3:
            return {"error": "Неверный формат даты. Ожидается формат: дд.мм.гггг"}
        
        day, month, year = date_parts
        
        # Проверяем наличие дня и месяца
        if not day or not month:
            return {"error": "Не указан месяц или число!"}
        
        # Если год не указан, указан не полностью или это двузначный год, используем текущий год
        if not year or len(year) < 4:
            current_year = datetime.now().year
            year = str(current_year)
        elif len(year) == 2:
            # Если год указан как двузначный (например, "24"), используем текущий год
            current_year = datetime.now().year
            year = str(current_year)
        
        # Формируем полную дату
        full_date_str = f"{day.zfill(2)}.{month.zfill(2)}.{year}"
        
        # Парсим дату и время
        dt = datetime.strptime(f"{full_date_str} {time_str}", "%d.%m.%Y %H:%M")
        tz = pytz.timezone(TIMEZONE)
        start_datetime = tz.localize(dt)
        end_datetime = start_datetime + timedelta(hours=1)
        
    except ValueError as e:
        return {"error": f"Ошибка парсинга даты/времени: {e}"}
    except Exception as e:
        return {"error": f"Ошибка обработки даты: {e}"}

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
        return event
    except Exception as e:
        return {"error": str(e)}