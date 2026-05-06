from aiogram import Router

from app.bot.routers.user import menu, verify, events  # noqa: registers handlers on sub-routers

router = Router(name="user")
router.include_routers(
    menu.router,
    verify.router,
    events.router,
)
