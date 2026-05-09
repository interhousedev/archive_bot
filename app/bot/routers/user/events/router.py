from aiogram import Router

from app.bot.filters.user_verified import UserVerified

router = Router(name="events")
router.message.filter(UserVerified(verified=True))
router.callback_query.filter(UserVerified(verified=True))
