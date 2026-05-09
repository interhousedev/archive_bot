import uuid
from typing import Any

from app.bot.utilities.data_formatting import message_split
from app.domain.error import AppError

from aiogram import BaseMiddleware, Bot
from aiogram.types import TelegramObject


class ErrorMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler,
        event: TelegramObject,
        data: dict[str, Any],
    ):
        try:
            return await handler(event, data)

        except Exception as e:
            basic_errors = [
                "Telegram server says - Bad Request: query is too old and "
                "response timeout expired or query ID is invalid"
            ]
            if str(e) in basic_errors:
                return None

            error_uuid = str(uuid.uuid4())
            bot: Bot = data["bot"]

            if isinstance(e, AppError):
                client_message = e.description
                support_data = e.description
                notify_user = True
            else:
                client_message = str(e)
                support_data = str(e)
                notify_user = True

            settings = data.get("container") and data["container"].settings
            admins_ids = settings.admins_ids if settings else None

            for admin_id in admins_ids:
                try:
                    for msg in message_split(text=support_data, type_="error", uuid_=error_uuid):
                        await bot.send_message(admin_id, msg)
                    for msg in message_split(text=str(event), type_="event", uuid_=error_uuid):
                        await bot.send_message(admin_id, msg)
                except Exception as e2:
                    print(error_uuid, e2)

            if notify_user:
                text = (
                    f"⚠️ An error occurred while handling your request.\n\n"
                    f"ERROR: {client_message}\n\n"
                    f"UUID: {error_uuid}"
                )
                user = data.get("event_from_user")
                if user:
                    try:
                        await bot.send_message(user.id, text)
                    except Exception:
                        pass

            return None
