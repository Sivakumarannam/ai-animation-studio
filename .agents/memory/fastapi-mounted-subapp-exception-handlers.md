---
name: FastAPI mounted sub-app exception handlers don't inherit from parent
description: When an API is versioned via app.mount("/api/v1", v1_app) with v1_app as its own FastAPI() instance, exception handlers registered on the outer app do not apply to routes inside the mounted sub-app.
---

If a FastAPI project versions its API by creating a separate `FastAPI()` instance
(e.g. `v1 = FastAPI(...)`) and mounting it with `app.mount(API_V1_PREFIX, v1)`,
any `@app.exception_handler(...)` registered on the outer `app` is silently
ignored for requests handled by `v1`'s routers. Domain exceptions (e.g. a custom
`NotFoundError`/`AppError` hierarchy) that are supposed to map to 404/409/422
instead surface as raw unhandled 500s from routes on the sub-app, even though
the exact same exception is correctly mapped when raised from the outer app.

**Why:** Starlette's `Mount` treats the mounted app as an independent ASGI
application with its own middleware/exception stack; it does not walk up to
the parent's exception handler registry. This is easy to miss because most
routers (e.g. ones that manually `try/except NotFoundError: raise
HTTPException(404, ...)` in each endpoint) mask the issue, while newer routers
that rely on the global handler expose it.

**How to apply:** When you see a domain exception unexpectedly returning 500
instead of its mapped status code, check whether routes are on a mounted
sub-app. Fix by registering the same exception handler(s) on the sub-app
instance too (e.g. `@v1.exception_handler(AppError)` calling the same handler
function), rather than wrapping every endpoint in manual try/except.
