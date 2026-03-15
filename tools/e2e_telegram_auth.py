import time
import json
import hashlib
import hmac
from urllib.parse import urlencode
import requests
from app.config import get_settings
def make_initdata(bot_token: str, user_id: int = 123456789, username: str = 'e2e_test'):
    auth_date = int(time.time())
    user_obj = {"id": user_id, "first_name": "E2E", "username": username}
    data = {
        'id': str(user_id),
        'first_name': user_obj['first_name'],
        'username': user_obj['username'],
        'auth_date': str(auth_date),
        'user': json.dumps(user_obj, separators=(',', ':')),
    }
    check_parts = []
    for key in sorted(data.keys()):
        check_parts.append(f"{key}={data[key]}")
    check_string = "\n".join(check_parts)
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    computed_hash = hmac.new(secret_key, check_string.encode(), hashlib.sha256).hexdigest()
    data['hash'] = computed_hash
    return urlencode(data)
def run_test():
    settings = get_settings()
    bot_token = settings.telegram_bot_token
    if not bot_token:
        print("TELEGRAM_BOT_TOKEN not configured in settings; aborting")
        return 1
    init_data = make_initdata(bot_token=bot_token, user_id=999999, username='e2e_test_user')
    url = 'http://127.0.0.1:8000/api/v1/auth/telegram/login'
    print(f"POSTing to {url} with init_data: {init_data[:80]}...")
    resp = requests.post(url, json={'init_data': init_data}, timeout=10)
    print('Status:', resp.status_code)
    try:
        print('Body:', resp.json())
    except Exception:
        print('Body (text):', resp.text[:1000])
    return 0
if __name__ == '__main__':
    raise SystemExit(run_test())
