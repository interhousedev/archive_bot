from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject


class UserRegisterMiddleware(BaseMiddleware):
    """Auto-create user record on first contact and inject it into handler data."""

    async def __call__(
        self,
        handler,
        event: TelegramObject,
        data: dict[str, Any],
    ):
        from_user = data.get("event_from_user")
        container = data.get("container")

        if from_user and container:
            user = await container.user_service.get_by_telegram_id(from_user.id)
            if user is None:
                user = await container.user_service.create(telegram_id=from_user.id)
            data["user"] = user

        return await handler(event, data)
