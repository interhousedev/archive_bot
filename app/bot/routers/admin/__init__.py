from app.bot.filters.is_admin import IsAdmin
from app.bot.routers.admin.router import router
from app.bot.routers.admin import create_event, manage_events, event_files, moderation  # noqa: registers handlers

router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())
