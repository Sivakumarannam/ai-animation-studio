from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool


def create_engine(
    database_url: str,
    pool_size: int = 10,
    max_overflow: int = 20,
    use_null_pool: bool = False,
):
    """
    Create an async SQLAlchemy engine.

    Pass `use_null_pool=True` in Celery worker processes so that every
    `session_scope()` call opens and closes its own connection.  This
    avoids the "Future attached to a different loop" error that occurs
    when asyncpg connections from the parent-process pool are reused
    inside `asyncio.run()` invocations spawned by `_run_async()`.
    """
    kwargs: dict[str, Any] = {"pool_pre_ping": True, "echo": False}
    if use_null_pool:
        kwargs["poolclass"] = NullPool
    else:
        kwargs["pool_size"] = pool_size
        kwargs["max_overflow"] = max_overflow
    return create_async_engine(database_url, **kwargs)


def create_session_factory(engine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


_engine = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def init_db(
    database_url: str,
    pool_size: int = 10,
    max_overflow: int = 20,
    use_null_pool: bool = False,
) -> None:
    global _engine, _session_factory
    _engine = create_engine(database_url, pool_size, max_overflow, use_null_pool=use_null_pool)
    _session_factory = create_session_factory(_engine)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    if _session_factory is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def session_scope() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager for database sessions — safe to use in Celery task
    core functions where `return` inside `async for session in get_session()`
    would abandon the generator and skip the commit.

    Catches BaseException (not just Exception) so that asyncio.CancelledError
    and KeyboardInterrupt also trigger an explicit rollback before re-raising.

    Usage:
        async with session_scope() as session:
            ...
            return result   # commit() runs synchronously on block exit
    """
    if _session_factory is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except BaseException:
            await session.rollback()
            raise


async def close_db() -> None:
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
