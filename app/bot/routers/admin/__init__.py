from app.bot.filters.is_admin import IsAdmin
from app.bot.routers.admin.router import router
from app.bot.routers.admin import events  # noqa: registers handlers on router

router.message.filter(IsAdmin())
