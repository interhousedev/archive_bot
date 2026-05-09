from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.routers.admin.callbacks import (
    AdminNoop,
    ManageBack,
    ManageDelete,
    ManageDeleteConfirm,
    ManageEditField,
    ManageEventFiles,
    ManageFileDelete,
    ManageFileDeleteConfirm,
    ManageFileDetail,
    ManageFileToggleBan,
    ManageSelectEvent,
)
from app.domain.file_type import FileType

_PAGE_SIZE = 20


def _type_icon(ft: FileType) -> str:
    return {"IMAGE": "🖼", "VIDEO": "🎬", "FILE": "📄"}.get(ft.value, "📎")


def _file_status(f) -> str:
    if f.is_banned:
        return "🚫"
    return "✅" if f.is_showed else "🙈"


def event_list_kb(events) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for ev in sorted(events, key=lambda e: e.date, reverse=True):
        builder.row(InlineKeyboardButton(
            text=f"{ev.name} — {ev.date.strftime('%d.%m.%Y')}",
            callback_data=ManageSelectEvent(event_id=ev.id).pack(),
        ))
    builder.row(InlineKeyboardButton(text="✖️ Close", callback_data=AdminNoop().pack()))
    return builder.as_markup()


def event_detail_kb(event_id: str, photos_count: int = 0) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✏️ Name",
            callback_data=ManageEditField(event_id=event_id, field="name").pack(),
        ),
        InlineKeyboardButton(
            text="📅 Date",
            callback_data=ManageEditField(event_id=event_id, field="date").pack(),
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="📝 Description",
            callback_data=ManageEditField(event_id=event_id, field="description").pack(),
        ),
        InlineKeyboardButton(
            text="🗑 Delete event",
            callback_data=ManageDelete(event_id=event_id).pack(),
        ),
    )
    builder.row(InlineKeyboardButton(
        text=f"📁 Files ({photos_count})",
        callback_data=ManageEventFiles(event_id=event_id, page=0).pack(),
    ))
    builder.row(InlineKeyboardButton(text="« Back", callback_data=ManageBack().pack()))
    return builder.as_markup()


def edit_cancel_kb(event_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="« Cancel",
        callback_data=ManageSelectEvent(event_id=event_id).pack(),
    ))
    return builder.as_markup()


def delete_confirm_kb(event_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Yes, delete",
            callback_data=ManageDeleteConfirm(event_id=event_id).pack(),
        ),
        InlineKeyboardButton(
            text="✖️ Cancel",
            callback_data=ManageSelectEvent(event_id=event_id).pack(),
        ),
    )
    return builder.as_markup()


def event_files_kb(files, event_id: str, page: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    total = len(files)
    total_pages = max(1, (total + _PAGE_SIZE - 1) // _PAGE_SIZE)
    page_files = files[page * _PAGE_SIZE:(page + 1) * _PAGE_SIZE]

    for i, f in enumerate(page_files, page * _PAGE_SIZE + 1):
        name = (f.original_name or f.file_name)[:24]
        builder.row(InlineKeyboardButton(
            text=f"{i}. {_type_icon(f.type)} {name} {_file_status(f)}",
            callback_data=ManageFileDetail(file_id=f.id, page=page).pack(),
        ))

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(
            text="◀",
            callback_data=ManageEventFiles(event_id=event_id, page=page - 1).pack(),
        ))
    nav.append(InlineKeyboardButton(
        text=f"{page + 1}/{total_pages}",
        callback_data=AdminNoop().pack(),
    ))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton(
            text="▶",
            callback_data=ManageEventFiles(event_id=event_id, page=page + 1).pack(),
        ))
    builder.row(*nav)
    builder.row(InlineKeyboardButton(
        text="« Back to event",
        callback_data=ManageSelectEvent(event_id=event_id).pack(),
    ))
    return builder.as_markup()


def file_action_kb(f, page: int, presigned_url: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔗 Open file (7 days)", url=presigned_url))
    builder.row(InlineKeyboardButton(
        text="👁 Show in gallery" if f.is_banned else "🙈 Hide from gallery",
        callback_data=ManageFileToggleBan(file_id=f.id, page=page).pack(),
    ))
    builder.row(InlineKeyboardButton(
        text="🗑 Delete from S3",
        callback_data=ManageFileDelete(file_id=f.id, page=page).pack(),
    ))
    builder.row(InlineKeyboardButton(
        text="« Back to files",
        callback_data=ManageEventFiles(event_id=f.event_id, page=page).pack(),
    ))
    return builder.as_markup()


def file_delete_confirm_kb(file_id: str, page: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Yes, delete",
            callback_data=ManageFileDeleteConfirm(file_id=file_id, page=page).pack(),
        ),
        InlineKeyboardButton(
            text="✖️ Cancel",
            callback_data=ManageFileDetail(file_id=file_id, page=page).pack(),
        ),
    )
    return builder.as_markup()