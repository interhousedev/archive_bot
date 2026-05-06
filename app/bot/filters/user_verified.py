from app.domain.user import User

from aiogram.filters import Filter
from aiogram.types import TelegramObject


class UserVerified(Filter):
    """Filter: checks injected user's verification status (set by UserRegisterMiddleware)."""

    def __init__(self, verified: bool) -> None:
        self.verified = verified

    async def __call__(self, event: TelegramObject, user: User = None) -> bool:
        if user is None:
            return not self.verified
        return user.is_verified is self.verified
