from aiogram import Dispatcher


def register_handlers(dispatcher: Dispatcher) -> None:
    from app.bot.routers import default
    from app.bot.routers.admin import router as admin_router
    from app.bot.routers.user import router as user_router

    dispatcher.include_routers(
        default.router,
        admin_router,
        user_router,
    )
