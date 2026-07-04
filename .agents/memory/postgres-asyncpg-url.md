---
name: PostgreSQL asyncpg URL quirks
description: Two URL issues that prevent asyncpg from connecting in Replit — wrong driver prefix and sslmode param.
---

## Rule
When reading `DATABASE_URL` from the Replit environment, always normalize it before passing to SQLAlchemy's `create_async_engine`. Two transforms are required:

1. **Driver prefix**: Replit's managed PostgreSQL sets `DATABASE_URL=postgresql://...` (no driver). asyncpg needs `postgresql+asyncpg://...`. Strip `postgresql://` or `postgres://` and prepend `postgresql+asyncpg://`.

2. **sslmode param**: Replit's URL includes `?sslmode=require` (or similar). asyncpg doesn't accept `sslmode` as a query parameter — it raises `TypeError: connect() got an unexpected keyword argument 'sslmode'`. Strip the `sslmode` key from the query string.

## Where to apply
- `backend/apps/api/config.py` — `Settings.normalize_db_url` field_validator on `DATABASE_URL`
- `backend/alembic/env.py` — `_normalize_db_url()` helper called when reading env var

## How to apply
```python
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse

def normalize_db_url(url: str) -> str:
    for prefix in ("postgresql://", "postgres://"):
        if url.startswith(prefix):
            url = "postgresql+asyncpg://" + url[len(prefix):]
            break
    parsed = urlparse(url)
    params = parse_qs(parsed.query, keep_blank_values=True)
    params.pop("sslmode", None)
    new_query = urlencode({k: v[0] for k, v in params.items()})
    return urlunparse(parsed._replace(query=new_query))
```

**Why:** Replit injects DATABASE_URL as a plain sync URL. SQLAlchemy without `+asyncpg` tries to use psycopg2, which isn't installed. The sslmode param is psycopg2-style syntax that asyncpg rejects entirely.
