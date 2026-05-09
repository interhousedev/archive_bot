from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.routers.user.events.callbacks import (
    FileAction,
    ListMyFiles,
    SelectEvent,
    StartUpload,
    ToggleFile,
)
from app.bot.routers.user.menu import OpenEvents, OpenMenu
from app.domain.file_type import FileType


def event_list_kb(events) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for ev in events:
        builder.row(InlineKeyboardButton(
            text=f"{ev.name} — {ev.date.strftime('%d.%m.%Y')} ({ev.photos_count} 📎)",
            callback_data=SelectEvent(event_id=ev.id).pack(),
        ))
    builder.row(InlineKeyboardButton(text="« Back", callback_data=OpenMenu().pack()))
    return builder.as_markup()


def event_detail_kb(event_id: str, event_url: str | None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="📤 Upload file",
        callback_data=StartUpload(event_id=event_id).pack(),
    ))
    builder.row(InlineKeyboardButton(
        text="📋 My files",
        callback_data=ListMyFiles(event_id=event_id).pack(),
    ))
    if event_url:
        builder.row(InlineKeyboardButton(text="🌐 View gallery", url=event_url))
    builder.row(InlineKeyboardButton(text="« Back", callback_data=OpenEvents().pack()))
    return builder.as_markup()


def upload_prompt_kb(event_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✅ Done", callback_data=OpenMenu().pack()))
    builder.row(InlineKeyboardButton(
        text="« Back",
        callback_data=SelectEvent(event_id=event_id).pack(),
    ))
    return builder.as_markup()


def my_files_list_kb(files, event_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for i, f in enumerate(files, 1):
        vis = "✅" if f.is_showed else "🙈"
        name = f.original_name or f.file_name
        icon = _type_icon(f.type)
        builder.row(InlineKeyboardButton(
            text=f"{i}. {icon} {name[:28]} {vis}",
            callback_data=FileAction(file_id=f.id).pack(),
        ))
    builder.row(InlineKeyboardButton(
        text="« Back",
        callback_data=SelectEvent(event_id=event_id).pack(),
    ))
    return builder.as_markup()


def file_detail_kb(file_id: str, event_id: str, is_showed: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="🙈 Hide" if is_showed else "👁 Show",
        callback_data=ToggleFile(file_id=file_id).pack(),
    ))
    builder.row(InlineKeyboardButton(
        text="« Back",
        callback_data=ListMyFiles(event_id=event_id).pack(),
    ))
    return builder.as_markup()


def _type_icon(ft: FileType) -> str:
    return {"IMAGE": "🖼", "VIDEO": "🎬", "FILE": "📄"}.get(ft.value, "📎")