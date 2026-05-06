from app.bootstrap import Container

from aiogram.filters import Filter
from aiogram.types import TelegramObject


class IsAdmin(Filter):
    """Filter: passes only if user's Telegram ID matches admins_ids in settings."""

    async def __call__(self, event: TelegramObject, container: Container) -> bool:
        from_user = getattr(event, "from_user", None)
        if from_user is None:
            return False
        return from_user.id in container.settings.admins_ids
