from datetime import datetime, timedelta, timezone
from uuid import UUID

from apps.api.config import Settings
from database.models.user import User
from packages.core.exceptions import AuthenticationError, ConflictError
from packages.utils.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from repositories.user_repository import RefreshTokenRepository, UserRepository


class AuthService:
    def __init__(
        self,
        user_repo: UserRepository,
        token_repo: RefreshTokenRepository,
        settings: Settings,
    ) -> None:
        self._user_repo = user_repo
        self._token_repo = token_repo
        self._settings = settings

    async def register(self, email: str, password: str, full_name: str) -> User:
        if await self._user_repo.email_exists(email):
            raise ConflictError(f"Email '{email}' is already registered")
        user = User(
            email=email,
            hashed_password=hash_password(password),
            full_name=full_name,
        )
        return await self._user_repo.create(user)

    async def login(self, email: str, password: str) -> tuple[str, str]:
        user = await self._user_repo.get_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            raise AuthenticationError("Invalid email or password")
        if not user.is_active:
            raise AuthenticationError("Account is deactivated")
        return await self._issue_tokens(user)

    async def refresh(self, refresh_token_str: str) -> tuple[str, str]:
        try:
            payload = decode_token(
                refresh_token_str,
                self._settings.SECRET_KEY,
                self._settings.JWT_ALGORITHM,
            )
        except ValueError as e:
            raise AuthenticationError(str(e)) from e

        if payload.get("type") != "refresh":
            raise AuthenticationError("Invalid token type")

        jti = payload.get("jti")
        if not jti:
            raise AuthenticationError("Malformed token")

        stored = await self._token_repo.get_by_jti(jti)
        if stored is None:
            raise AuthenticationError("Token has been revoked")

        if stored.expires_at < datetime.now(timezone.utc):
            raise AuthenticationError("Refresh token expired")

        user_id = UUID(payload["sub"])
        user = await self._user_repo.get_by_id(user_id)
        if user is None or not user.is_active:
            raise AuthenticationError("User not found or inactive")

        await self._token_repo.revoke_by_jti(jti)
        return await self._issue_tokens(user)

    async def logout(self, refresh_token_str: str) -> None:
        try:
            payload = decode_token(
                refresh_token_str,
                self._settings.SECRET_KEY,
                self._settings.JWT_ALGORITHM,
            )
            jti = payload.get("jti")
            if jti:
                await self._token_repo.revoke_by_jti(jti)
        except ValueError:
            pass

    async def get_current_user(self, user_id: UUID) -> User:
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise AuthenticationError("User not found")
        return user

    async def _issue_tokens(self, user: User) -> tuple[str, str]:
        data = {"sub": str(user.id)}
        access_token = create_access_token(
            data,
            self._settings.SECRET_KEY,
            self._settings.JWT_ALGORITHM,
            self._settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        )
        refresh_token_str, jti = create_refresh_token(
            data,
            self._settings.SECRET_KEY,
            self._settings.JWT_ALGORITHM,
            self._settings.REFRESH_TOKEN_EXPIRE_DAYS,
        )
        expires_at = datetime.now(timezone.utc) + timedelta(days=self._settings.REFRESH_TOKEN_EXPIRE_DAYS)
        await self._token_repo.create(user.id, jti, refresh_token_str, expires_at)
        return access_token, refresh_token_str
