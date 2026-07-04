from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

import bcrypt
import jwt


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def create_access_token(
    data: dict[str, Any],
    secret_key: str,
    algorithm: str,
    expires_minutes: int,
) -> str:
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    payload.update({"exp": expire, "type": "access"})
    return jwt.encode(payload, secret_key, algorithm=algorithm)


def create_refresh_token(
    data: dict[str, Any],
    secret_key: str,
    algorithm: str,
    expires_days: int,
) -> tuple[str, str]:
    payload = data.copy()
    jti = str(uuid4())
    expire = datetime.now(timezone.utc) + timedelta(days=expires_days)
    payload.update({"exp": expire, "type": "refresh", "jti": jti})
    token = jwt.encode(payload, secret_key, algorithm=algorithm)
    return token, jti


def decode_token(token: str, secret_key: str, algorithm: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, secret_key, algorithms=[algorithm])
    except jwt.PyJWTError as e:
        raise ValueError(f"Invalid token: {e}") from e
