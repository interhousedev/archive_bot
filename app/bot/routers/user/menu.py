from app.bootstrap import Container
from app.domain.user import User

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData

router = Router(name="menu")


class OpenMenu(CallbackData, prefix="open_menu"):
    pass


class StartVerify(CallbackData, prefix="start_verify"):
    pass


class OpenEvents(CallbackData, prefix="open_events"):
    pass


def _menu_keyboard(is_verified: bool, webapp_url: str | None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if webapp_url:
        builder.row(InlineKeyboardButton(
            text="🌐 View Photos",
            web_app=WebAppInfo(url=webapp_url),
        ))

    if is_verified:
        builder.row(InlineKeyboardButton(
            text="📸 Add images",
            callback_data=OpenEvents().pack(),
        ))
    else:
        builder.row(InlineKeyboardButton(
            text="✅ Verify yourself",
            callback_data=StartVerify().pack(),
        ))

    return builder.as_markup()


@router.message(CommandStart(), F.chat.type == "private")
async def start(message: Message, container: Container, user: User) -> None:
    webapp_url = container.settings.webapp_base_url

    if user.is_verified:
        text = "👋 Welcome back to Memory Archive!"
    else:
        text = (
            "👋 Welcome to Memory Archive!\n\n"
            "To upload photos you need to verify your student status first."
        )

    await message.answer(text, reply_markup=_menu_keyboard(user.is_verified, webapp_url))


@router.callback_query(OpenMenu.filter())
async def back_to_menu(callback, container: Container, user: User) -> None:
    webapp_url = container.settings.webapp_base_url

    if user.is_verified:
        text = "👋 Welcome back to Memory Archive!"
    else:
        text = (
            "👋 Welcome to Memory Archive!\n\n"
            "To upload photos you need to verify your student status first."
        )

    await callback.message.edit_text(
        text, reply_markup=_menu_keyboard(user.is_verified, webapp_url)
    )
