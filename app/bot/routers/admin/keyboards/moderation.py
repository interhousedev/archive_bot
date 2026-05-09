from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.routers.admin.callbacks import AdminBanFile, AdminToggleSender, AdminUnbanFile


def admin_notification_kb(
    file_id: str,
    author_telegram_id: int,
    file_banned: bool,
    sender_banned: bool,
    presigned_url: str,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔗 Open file (7 days)", url=presigned_url))
    file_btn = InlineKeyboardButton(
        text="↩️ Unhide file" if file_banned else "🚫 Ban file",
        callback_data=AdminUnbanFile(file_id=file_id, author_telegram_id=author_telegram_id).pack()
        if file_banned
        else AdminBanFile(file_id=file_id, author_telegram_id=author_telegram_id).pack(),
    )
    sender_btn = InlineKeyboardButton(
        text="↩️ Unban sender" if sender_banned else "🚫 Ban sender",
        callback_data=AdminToggleSender(
            file_id=file_id, author_telegram_id=author_telegram_id
        ).pack(),
    )
    builder.row(file_btn, sender_btn)
    return builder.as_markup()