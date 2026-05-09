from datetime import datetime

from app.bootstrap import Container
from app.bot.routers.admin.callbacks import (
    ManageBack,
    ManageDelete,
    ManageDeleteConfirm,
    ManageEditField,
    ManageSelectEvent,
)
from app.bot.routers.admin.keyboards.events import (
    delete_confirm_kb,
    edit_cancel_kb,
    event_detail_kb,
    event_list_kb,
)
from app.bot.routers.admin.router import router

from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery


class ManageEventStates(StatesGroup):
    editing_name = State()
    editing_date = State()
    editing_description = State()


def _event_detail_text(ev) -> str:
    text = f"📅 {ev.name}\nDate: {ev.date.strftime('%d.%m.%Y')}\nFiles: {ev.photos_count}"
    if ev.description:
        text += f"\nDescription: {ev.description}"
    return text


@router.message(Command("manage_events"), StateFilter(None))
async def manage_events(message: Message, container: Container) -> None:
    events = await container.event_service.get_all()
    if not events:
        await message.answer("No events yet. Use /create_event to create one.")
        return
    await message.answer("📋 Select an event to manage:", reply_markup=event_list_kb(events))


@router.callback_query(ManageBack.filter())
async def manage_back(callback: CallbackQuery, container: Container) -> None:
    events = await container.event_service.get_all()
    if not events:
        await callback.message.edit_text("No events yet.")
        return
    await callback.message.edit_text(
        "📋 Select an event to manage:", reply_markup=event_list_kb(events)
    )


@router.callback_query(ManageSelectEvent.filter())
async def show_event_detail(
    callback: CallbackQuery,
    callback_data: ManageSelectEvent,
    state: FSMContext,
    container: Container,
) -> None:
    await state.clear()
    ev = await container.event_service.get_by_id(callback_data.event_id)
    if not ev:
        await callback.answer("Event not found.", show_alert=True)
        return
    await callback.message.edit_text(
        _event_detail_text(ev), reply_markup=event_detail_kb(ev.id, ev.photos_count)
    )


@router.callback_query(ManageEditField.filter(), StateFilter(None))
async def start_edit_field(
    callback: CallbackQuery, callback_data: ManageEditField, state: FSMContext,
) -> None:
    event_id = callback_data.event_id
    field = callback_data.field
    await state.update_data(event_id=event_id)

    prompts = {
        "name": "Enter new event name:",
        "date": "Enter new date (YYYY-MM-DD):",
        "description": "Enter new description:",
    }
    states = {
        "name": ManageEventStates.editing_name,
        "date": ManageEventStates.editing_date,
        "description": ManageEventStates.editing_description,
    }
    await state.set_state(states[field])
    await callback.message.edit_text(prompts[field], reply_markup=edit_cancel_kb(event_id))


@router.message(StateFilter(ManageEventStates.editing_name))
async def receive_new_name(message: Message, state: FSMContext, container: Container) -> None:
    data = await state.get_data()
    event_id = data["event_id"]
    await state.clear()
    await container.event_service.update(event_id, name=message.text.strip())
    ev = await container.event_service.get_by_id(event_id)
    await message.answer(
        "✅ Name updated!\n\n" + _event_detail_text(ev),
        reply_markup=event_detail_kb(event_id, ev.photos_count),
    )


@router.message(StateFilter(ManageEventStates.editing_date))
async def receive_new_date(message: Message, state: FSMContext, container: Container) -> None:
    try:
        date = datetime.strptime(message.text.strip(), "%Y-%m-%d")
    except ValueError:
        await message.reply("Invalid date. Use YYYY-MM-DD.")
        return
    data = await state.get_data()
    event_id = data["event_id"]
    await state.clear()
    await container.event_service.update(event_id, date=date)
    ev = await container.event_service.get_by_id(event_id)
    await message.answer(
        "✅ Date updated!\n\n" + _event_detail_text(ev),
        reply_markup=event_detail_kb(event_id, ev.photos_count),
    )


@router.message(StateFilter(ManageEventStates.editing_description))
async def receive_new_description(message: Message, state: FSMContext, container: Container) -> None:
    data = await state.get_data()
    event_id = data["event_id"]
    await state.clear()
    await container.event_service.update(event_id, description=message.text.strip())
    ev = await container.event_service.get_by_id(event_id)
    await message.answer(
        "✅ Description updated!\n\n" + _event_detail_text(ev),
        reply_markup=event_detail_kb(event_id, ev.photos_count),
    )


@router.callback_query(ManageDelete.filter(), StateFilter(None))
async def confirm_delete(
    callback: CallbackQuery, callback_data: ManageDelete, container: Container,
) -> None:
    ev = await container.event_service.get_by_id(callback_data.event_id)
    if not ev:
        await callback.answer("Event not found.", show_alert=True)
        return
    await callback.message.edit_text(
        f'🗑 Delete "{ev.name}" ({ev.date.strftime("%d.%m.%Y")})?\n\nThis cannot be undone.',
        reply_markup=delete_confirm_kb(callback_data.event_id),
    )


@router.callback_query(ManageDeleteConfirm.filter())
async def do_delete(
    callback: CallbackQuery, callback_data: ManageDeleteConfirm, container: Container,
) -> None:
    await container.event_service.delete(callback_data.event_id)
    events = await container.event_service.get_all()
    if not events:
        await callback.message.edit_text("✅ Event deleted. No events remaining.")
        return
    await callback.message.edit_text(
        "✅ Event deleted.\n\n📋 Select an event to manage:",
        reply_markup=event_list_kb(events),
    )