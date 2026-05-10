import uuid
from datetime import datetime

from app.bootstrap import Container
from app.bot.routers.admin.callbacks import (
    CreateCancel, CreateNewCategory, CreateSelectCategory, CreateSkipDescription,
)
from app.bot.routers.admin.router import router

from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


class CreateEventStates(StatesGroup):
    waiting_category_choice = State()
    waiting_category_name = State()
    waiting_name = State()
    waiting_date = State()
    waiting_description = State()


def _cancel_kb():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✖️ Cancel", callback_data=CreateCancel().pack()))
    return builder.as_markup()


async def _category_kb(container: Container):
    categories = await container.category_service.get_all()
    builder = InlineKeyboardBuilder()
    for cat in sorted(categories, key=lambda c: c.name):
        builder.row(InlineKeyboardButton(
            text=cat.name,
            callback_data=CreateSelectCategory(category_id=cat.id).pack(),
        ))
    builder.row(InlineKeyboardButton(text="➕ New category", callback_data=CreateNewCategory().pack()))
    builder.row(InlineKeyboardButton(text="✖️ Cancel", callback_data=CreateCancel().pack()))
    return builder.as_markup()


@router.message(Command("create_event"), StateFilter(None))
async def create_event_start(message: Message, state: FSMContext, container: Container) -> None:
    await state.set_state(CreateEventStates.waiting_category_choice)
    await message.answer("Select a category for the event:", reply_markup=await _category_kb(container))


@router.callback_query(CreateSelectCategory.filter(), StateFilter(CreateEventStates.waiting_category_choice))
async def create_select_category(
    callback: CallbackQuery, callback_data: CreateSelectCategory, state: FSMContext
) -> None:
    await state.update_data(category_id=callback_data.category_id)
    await state.set_state(CreateEventStates.waiting_name)
    await callback.message.edit_text("Enter event name:", reply_markup=_cancel_kb())


@router.callback_query(CreateNewCategory.filter(), StateFilter(CreateEventStates.waiting_category_choice))
async def create_new_category_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(CreateEventStates.waiting_category_name)
    await callback.message.edit_text("Enter new category name:", reply_markup=_cancel_kb())


@router.message(StateFilter(CreateEventStates.waiting_category_name))
async def create_category_name(message: Message, state: FSMContext, container: Container) -> None:
    category = await container.category_service.create(name=message.text.strip())
    await state.update_data(category_id=category.id)
    await state.set_state(CreateEventStates.waiting_name)
    await message.answer(
        f'Category "{category.name}" created.\nEnter event name:',
        reply_markup=_cancel_kb(),
    )


@router.message(StateFilter(CreateEventStates.waiting_name))
async def create_event_name(message: Message, state: FSMContext) -> None:
    await state.update_data(name=message.text.strip())
    await state.set_state(CreateEventStates.waiting_date)
    await message.answer("Enter date (YYYY-MM-DD):", reply_markup=_cancel_kb())


@router.message(StateFilter(CreateEventStates.waiting_date))
async def create_event_date(message: Message, state: FSMContext) -> None:
    try:
        date = datetime.strptime(message.text.strip(), "%Y-%m-%d")
    except ValueError:
        await message.reply("Invalid date. Use YYYY-MM-DD format.")
        return
    await state.update_data(date=date)
    await state.set_state(CreateEventStates.waiting_description)
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="⏭ Skip", callback_data=CreateSkipDescription().pack()),
        InlineKeyboardButton(text="✖️ Cancel", callback_data=CreateCancel().pack()),
    )
    await message.answer("Enter description (or skip):", reply_markup=builder.as_markup())


async def _finish_create(data: dict, container: Container, description: str | None = None) -> str:
    event = await container.event_service.create(
        name=data["name"],
        date=data["date"],
        images_folder=str(uuid.uuid4()),
        category_id=data["category_id"],
        description=description,
    )
    raw_id = event.id.replace("-", "")
    slug = raw_id[:4] + raw_id[-8:]
    return (
        f"✅ Event created!\n"
        f"Name: {event.name}\n"
        f"Date: {event.date.strftime('%d.%m.%Y')}\n"
        f"Slug: {slug}\n"
        f"S3 folder: {event.images_folder}"
    )


@router.message(StateFilter(CreateEventStates.waiting_description))
async def create_event_description(message: Message, state: FSMContext, container: Container) -> None:
    data = await state.get_data()
    await state.clear()
    text = await _finish_create(data, container, description=message.text.strip() if message.text else None)
    await message.answer(text)


@router.callback_query(CreateSkipDescription.filter())
async def create_skip_description(callback: CallbackQuery, state: FSMContext, container: Container) -> None:
    data = await state.get_data()
    await state.clear()
    text = await _finish_create(data, container)
    await callback.message.edit_text(text)


@router.callback_query(CreateCancel.filter())
async def create_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("Event creation cancelled.")