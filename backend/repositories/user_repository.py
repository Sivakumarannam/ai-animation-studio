from datetime import datetime, timezone
from hashlib import sha256

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.user import RefreshToken, User
from repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def email_exists(self, email: str) -> bool:
        return await self.get_by_email(email) is not None


class RefreshTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _hash_token(token: str) -> str:
        return sha256(token.encode()).hexdigest()

    async def create(self, user_id, jti: str, raw_token: str, expires_at: datetime) -> RefreshToken:
        token = RefreshToken(
            user_id=user_id,
            jti=jti,
            token_hash=self._hash_token(raw_token),
            expires_at=expires_at,
            created_at=datetime.now(timezone.utc),
        )
        self._session.add(token)
        await self._session.flush()
        return token

    async def get_by_jti(self, jti: str) -> RefreshToken | None:
        stmt = select(RefreshToken).where(RefreshToken.jti == jti)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def revoke_by_jti(self, jti: str) -> None:
        token = await self.get_by_jti(jti)
        if token:
            await self._session.delete(token)
            await self._session.flush()

    async def revoke_all_for_user(self, user_id) -> None:
        stmt = select(RefreshToken).where(RefreshToken.user_id == user_id)
        result = await self._session.execute(stmt)
        for token in result.scalars():
            await self._session.delete(token)
        await self._session.flush()
