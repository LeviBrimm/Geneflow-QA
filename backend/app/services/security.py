import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta

from app.config.settings import get_settings


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000)
    return f"pbkdf2_sha256${salt}${digest.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        scheme, salt, expected = password_hash.split("$", 2)
    except ValueError:
        return False
    if scheme != "pbkdf2_sha256":
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000).hex()
    return hmac.compare_digest(digest, expected)


def create_access_token(user_id: int, email: str) -> str:
    settings = get_settings()
    payload = {
        "sub": user_id,
        "email": email,
        "exp": (datetime.utcnow() + timedelta(minutes=settings.access_token_minutes)).isoformat(),
    }
    body = _b64(json.dumps(payload, separators=(",", ":")).encode())
    signature = _sign(body, settings.auth_secret)
    return f"{body}.{signature}"


def decode_access_token(token: str) -> dict:
    settings = get_settings()
    try:
        body, signature = token.split(".", 1)
    except ValueError as exc:
        raise ValueError("Invalid token.") from exc
    if not hmac.compare_digest(_sign(body, settings.auth_secret), signature):
        raise ValueError("Invalid token signature.")
    payload = json.loads(base64.urlsafe_b64decode(_pad(body)).decode())
    if datetime.fromisoformat(payload["exp"]) < datetime.utcnow():
        raise ValueError("Token expired.")
    return payload


def _sign(body: str, secret: str) -> str:
    return _b64(hmac.new(secret.encode(), body.encode(), hashlib.sha256).digest())


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode().rstrip("=")


def _pad(value: str) -> bytes:
    return (value + "=" * (-len(value) % 4)).encode()
