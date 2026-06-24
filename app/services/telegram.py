import hashlib
import hmac
import json
from urllib.parse import parse_qs, unquote

from app.config import settings


def verify_telegram_init_data(init_data: str) -> dict | None:
    parsed = dict(parse_qs(init_data, keep_blank_values=True))
    if "hash" not in parsed:
        return None

    received_hash = parsed.pop("hash")[0]

    data_check_string = "\n".join(
        f"{k}={unquote(v[0])}" for k, v in sorted(parsed.items())
    )

    secret_key = hmac.new(b"WebAppData", settings.BOT_TOKEN.encode(), hashlib.sha256).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        return None

    user_data = parsed.get("user", [None])[0]
    if user_data:
        return json.loads(unquote(user_data))
    return None
