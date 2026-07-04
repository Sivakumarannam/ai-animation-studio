---
name: PyJWT vs python-jose
description: python-jose is firewall-blocked in Replit; use PyJWT==2.10.1 instead. Import syntax differs.
---

## Rule
Do NOT use `python-jose`. It is permanently blocked by Replit's package firewall (HTTP 403 on install).

Use `PyJWT==2.10.1` + `cryptography==44.0.0` instead.

## Import differences
```python
# jose (blocked - do not use)
from jose import JWTError, jwt

# PyJWT (correct)
import jwt
# error class:
except jwt.PyJWTError as e: ...
# encode/decode API is identical otherwise
```

**Why:** python-jose is on Replit's package firewall blocklist. cryptography package is needed for some JWT algorithms.
