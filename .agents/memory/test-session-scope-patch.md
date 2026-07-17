---
name: Unit test session_scope patch path
description: How to correctly mock session_scope in Celery task tests
---

## Rule
When session_scope is imported inside an async function body:
  `async def _core(...): from database.connection import session_scope; async with session_scope() as s:`

Patch it at: `database.connection.session_scope`  ← the source module
NOT at:      `apps.worker.tasks.mytasks.session_scope`  ← the importing module

**Why:** `from X import Y` inside a function runs at call time; it looks up Y on the
X module object in sys.modules. Patching the importing module's attribute fails with
AttributeError because session_scope was never assigned there at module level.

**How to apply:** In all Celery task end-to-end tests, use
  `with patch("database.connection.session_scope") as mock_scope:`
