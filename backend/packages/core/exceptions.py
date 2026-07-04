from typing import Any


class AppError(Exception):
    """Base application error."""

    def __init__(self, message: str, code: str = "APP_ERROR", detail: Any = None) -> None:
        self.message = message
        self.code = code
        self.detail = detail
        super().__init__(message)


class NotFoundError(AppError):
    def __init__(self, resource: str, resource_id: Any = None) -> None:
        msg = f"{resource} not found"
        if resource_id is not None:
            msg = f"{resource} with id '{resource_id}' not found"
        super().__init__(msg, "NOT_FOUND")


class ConflictError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, "CONFLICT")


class ValidationError(AppError):
    def __init__(self, message: str, detail: Any = None) -> None:
        super().__init__(message, "VALIDATION_ERROR", detail)


class AuthenticationError(AppError):
    def __init__(self, message: str = "Authentication failed") -> None:
        super().__init__(message, "AUTHENTICATION_ERROR")


class AuthorizationError(AppError):
    def __init__(self, message: str = "Insufficient permissions") -> None:
        super().__init__(message, "AUTHORIZATION_ERROR")


class PluginError(AppError):
    def __init__(self, plugin_name: str, message: str) -> None:
        super().__init__(f"[Plugin:{plugin_name}] {message}", "PLUGIN_ERROR")


class ProviderError(AppError):
    def __init__(self, provider: str, message: str) -> None:
        super().__init__(f"[Provider:{provider}] {message}", "PROVIDER_ERROR")


class StorageError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, "STORAGE_ERROR")


class PipelineError(AppError):
    def __init__(self, step: str, message: str) -> None:
        super().__init__(f"[Step:{step}] {message}", "PIPELINE_ERROR")
