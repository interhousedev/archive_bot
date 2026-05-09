import asyncio
import io
import os
import uuid
from pathlib import Path

from app.bootstrap import Container
from app.bot.routers.admin.keyboards.moderation import admin_notification_kb
from app.bot.routers.user.events.callbacks import StartUpload
from app.bot.routers.user.events.keyboards.events import upload_prompt_kb
from app.bot.routers.user.events.router import router
from app.bot.routers.user.menu import OpenMenu, _menu_keyboard
from app.domain.file_type import FileType
from app.domain.user import User

from aiogram import F, Bot
from aiogram.filters import StateFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery


class UploadStates(StatesGroup):
    waiting_file = State()


_EXTENSION_TO_TYPE: dict[str, FileType] = {
    ext: FileType.IMAGE
    for ext in ("jpg", "jpeg", "png", "gif", "webp", "bmp", "heic", "heif", "tiff")
} | {
    ext: FileType.VIDEO
    for ext in ("mp4", "mov", "avi", "mkv", "webm", "flv", "3gp", "wmv", "m4v")
}

_CONTENT_TYPES: dict[str, str] = {
    "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
    "gif": "image/gif", "webp": "image/webp", "bmp": "image/bmp",
    "heic": "image/heic", "heif": "image/heif", "tiff": "image/tiff",
    "mp4": "video/mp4", "mov": "video/quicktime", "avi": "video/x-msvideo",
    "mkv": "video/x-matroska", "webm": "video/webm", "flv": "video/x-flv",
    "3gp": "video/3gpp", "wmv": "video/x-ms-wmv", "m4v": "video/x-m4v",
    "pdf": "application/pdf",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "zip": "application/zip",
}


def _detect_type(filename: str) -> FileType:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return _EXTENSION_TO_TYPE.get(ext, FileType.FILE)


def _content_type(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return _CONTENT_TYPES.get(ext, "application/octet-stream")


def _extract_file_info(message: Message) -> tuple[str, str, int] | None:
    """Return (tg_file_id, original_filename, file_size) or None if no media."""
    if message.photo:
        p = message.photo[-1]
        return p.file_id, f"{uuid.uuid4()}.jpg", p.file_size or 0
    if message.document:
        d = message.document
        return d.file_id, d.file_name or f"{uuid.uuid4()}.bin", d.file_size or 0
    if message.video:
        v = message.video
        return v.file_id, v.file_name or f"{uuid.uuid4()}.mp4", v.file_size or 0
    if message.animation:
        a = message.animation
        return a.file_id, a.file_name or f"{uuid.uuid4()}.gif", a.file_size or 0
    if message.audio:
        a = message.audio
        return a.file_id, a.file_name or f"{uuid.uuid4()}.mp3", a.file_size or 0
    if message.voice:
        v = message.voice
        return v.file_id, f"{uuid.uuid4()}.ogg", v.file_size or 0
    return None


def _type_icon(ft: FileType) -> str:
    return {"IMAGE": "🖼", "VIDEO": "🎬", "FILE": "📄"}.get(ft.value, "📎")


async def _notify_admins(
    bot: Bot,
    container: Container,
    media_file,
    ev,
    author_telegram_id: int,
    author_username: str | None,
    tg_file_id: str,
) -> None:
    try:
        s3_key = f"{ev.images_folder}/{media_file.file_name}"
        presigned = await container.s3_client.presigned_url(s3_key, expires_seconds=7 * 86400)
        sender_label = f"@{author_username}" if author_username else f"ID: {author_telegram_id}"
        text = (
            f"📎 New file uploaded\n"
            f"📅 Event: {ev.name} — {ev.date.strftime('%d.%m.%Y')}\n"
            f"👤 Sender: {sender_label} (ID: {author_telegram_id})\n"
            f"🖼 Type: {media_file.type.value}"
        )
        kb = admin_notification_kb(
            file_id=media_file.id,
            author_telegram_id=author_telegram_id,
            file_banned=False,
            sender_banned=False,
            presigned_url=presigned,
        )
        for admin_id in container.settings.admins_ids:
            try:
                if media_file.type == FileType.IMAGE:
                    await bot.send_photo(
                        chat_id=admin_id, photo=tg_file_id, caption=text, reply_markup=kb,
                    )
                else:
                    await bot.send_message(chat_id=admin_id, text=text, reply_markup=kb)
            except Exception:
                pass
    except Exception:
        pass


@router.callback_query(StartUpload.filter(), StateFilter(None))
async def prompt_upload(
    callback: CallbackQuery, callback_data: StartUpload, state: FSMContext, user: User,
) -> None:
    if user.is_banned:
        await callback.answer("You are restricted from uploading.", show_alert=True)
        return
    await state.set_state(UploadStates.waiting_file)
    await state.update_data(event_id=callback_data.event_id)
    await callback.message.edit_text(
        "📎 Send your file(s) now — photos, videos, documents and more are accepted.\n\n"
        "Files are visible to everyone by default — you can hide them via 📋 My files.\n\n"
        "Press Done when finished.",
        reply_markup=upload_prompt_kb(callback_data.event_id),
    )


@router.message(
    StateFilter(UploadStates.waiting_file),
    F.photo | F.document | F.video | F.animation | F.audio | F.voice,
)
async def receive_file(
    message: Message, state: FSMContext, container: Container, bot: Bot, user: User,
) -> None:
    if user.is_banned:
        await message.reply("🚫 You are restricted from uploading.")
        return

    info = _extract_file_info(message)
    if not info:
        await message.reply("Unsupported file type.")
        return

    tg_file_id, original_name, _ = info

    data = await state.get_data()
    event_id = data["event_id"]
    ev = await container.event_service.get_by_id(event_id)
    if not ev:
        await message.reply("Event not found. Use /start to restart.")
        await state.clear()
        return

    tg_file = await bot.get_file(tg_file_id)
    abs_path = tg_file.file_path
    local_root = container.settings.botapi_local_files_path

    if abs_path and abs_path.startswith("/"):
        relative = abs_path.removeprefix("/var/lib/telegram-bot-api/")
        local_path = Path(local_root) / relative
        file_data = await asyncio.to_thread(local_path.read_bytes)
    else:
        buf = io.BytesIO()
        await bot.download_file(abs_path, buf)
        file_data = buf.getvalue()

    file_type = _detect_type(original_name)
    content_type = _content_type(original_name)
    ext = original_name.rsplit(".", 1)[-1] if "." in original_name else "bin"
    s3_filename = f"{uuid.uuid4()}.{ext}"

    await container.s3_client.upload(
        folder=ev.images_folder,
        filename=s3_filename,
        data=file_data,
        content_type=content_type,
    )
    media_file = await container.media_file_service.create(
        file_name=s3_filename,
        event_id=event_id,
        author_id=user.id,
        file_type=file_type,
        original_name=original_name,
    )
    await container.event_service.increment_photos_count(event_id)

    if abs_path and abs_path.startswith("/"):
        relative = abs_path.removeprefix("/var/lib/telegram-bot-api/")
        local_path = Path(container.settings.botapi_local_files_path) / relative
        await asyncio.to_thread(lambda: os.unlink(local_path) if local_path.exists() else None)

    await message.reply(
        f"✅ {_type_icon(file_type)} File uploaded!\n"
        "It's visible to everyone by default.\n"
        "You can hide it anytime via 📋 My files."
    )
    await _notify_admins(
        bot=bot,
        container=container,
        media_file=media_file,
        ev=ev,
        author_telegram_id=message.from_user.id,
        author_username=message.from_user.username,
        tg_file_id=tg_file_id,
    )


@router.message(StateFilter(UploadStates.waiting_file), Command("done"))
async def done_upload(
    message: Message, state: FSMContext, container: Container, user: User,
) -> None:
    await state.clear()
    await message.answer(
        "✅ Upload session ended.",
        reply_markup=_menu_keyboard(user.is_verified, container.settings.webapp_base_url, user.is_banned),
    )


@router.callback_query(OpenMenu.filter(), StateFilter(UploadStates.waiting_file))
async def done_upload_cb(
    callback: CallbackQuery, state: FSMContext, container: Container, user: User,
) -> None:
    await state.clear()
    await callback.message.edit_text(
        "👋 Welcome back to Memory Archive!",
        reply_markup=_menu_keyboard(user.is_verified, container.settings.webapp_base_url, user.is_banned),
    )