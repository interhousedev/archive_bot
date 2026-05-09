from app.bootstrap import Container
from app.bot.routers.user.events.callbacks import SelectEvent
from app.bot.routers.user.events.keyboards.events import event_detail_kb, event_list_kb
from app.bot.routers.user.events.router import router
from app.bot.routers.user.menu import OpenEvents

from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery


@router.callback_query(OpenEvents.filter(), StateFilter(None))
async def list_events(callback: CallbackQuery, container: Container) -> None:
    events = await container.event_service.get_all()
    if not events:
        await callback.answer("No events available yet.", show_alert=True)
        return
    events_sorted = sorted(events, key=lambda e: e.date, reverse=True)
    await callback.message.edit_text(
        "📋 Select an event:", reply_markup=event_list_kb(events_sorted)
    )


@router.callback_query(SelectEvent.filter(), StateFilter(None))
async def show_event(
    callback: CallbackQuery, callback_data: SelectEvent, container: Container,
) -> None:
    ev = await container.event_service.get_by_id(callback_data.event_id)
    if not ev:
        await callback.answer("Event not found.", show_alert=True)
        return

    raw_id = ev.id.replace("-", "")
    slug = raw_id[:4] + raw_id[-8:]
    webapp_url = container.settings.webapp_base_url
    event_url = f"{webapp_url}/{slug}" if webapp_url else None

    text = f"📅 {ev.name}\nDate: {ev.date.strftime('%d.%m.%Y')}\nFiles: {ev.photos_count}"
    await callback.message.edit_text(text, reply_markup=event_detail_kb(ev.id, event_url))