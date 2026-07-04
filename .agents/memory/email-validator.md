---
name: email-validator required for Pydantic EmailStr
description: Pydantic v2 EmailStr field requires separate email-validator package install.
---

## Rule
Whenever a Pydantic model uses `EmailStr`, add `email-validator==2.2.0` to `requirements.txt` and install it. Without it, the model raises `ImportError: email-validator is not installed` at schema generation time (not import time).

**Why:** Pydantic v2 separates the email validation library as an optional dependency to avoid adding DNS lookup dependencies to the core package.
