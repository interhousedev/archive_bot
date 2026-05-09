from app.bootstrap import Container
from app.bot.middlewares.error_handler import ErrorMiddleware
from app.bot.middlewares.user_register import UserRegisterMiddleware
from app.bot.routers import register_handlers

from aiogram import Dispatcher, Bot
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeChat


async def _set_admin_commands(bot: Bot, admin_ids: list[int]) -> None:
    commands = [
        BotCommand(command="start", description="Open menu"),
        BotCommand(command="create_event", description="Create new event"),
        BotCommand(command="manage_events", description="Manage events"),
    ]
    for admin_id in admin_ids:
        try:
            await bot.set_my_commands(commands, scope=BotCommandScopeChat(chat_id=admin_id))
        except Exception:
            pass


async def main(botapi_token: str, container: Container) -> None:
    if not botapi_token:
        raise ValueError("botapi_token is required")

    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher.update.outer_middleware(UserRegisterMiddleware())
    dispatcher.update.middleware(ErrorMiddleware())

    register_handlers(dispatcher)

    server_url = container.settings.botapi_server_url
    if server_url:
        from aiogram.client.telegram import TelegramAPIServer
        session = AiohttpSession(api=TelegramAPIServer.from_base(server_url))
        bot = Bot(token=botapi_token, session=session)
    else:
        bot = Bot(token=botapi_token)

    try:
        await _set_admin_commands(bot, container.settings.admins_ids)
        print("Bot started polling")
        await dispatcher.start_polling(bot, container=container)
    finally:
        await bot.session.close()
        print("Bot stopped")