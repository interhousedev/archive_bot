import asyncio
import io
import os
import uuid
from pathlib import Path

from app.bootstrap import Container
from app.domain.user import User
from app.domain.file_type import FileType
from app.bot.filters.user_verified import UserVerified
from app.bot.routers.user.menu import OpenEvents, OpenMenu, _menu_keyboard

from aiogram import F, Router, Bot
from aiogram.enums import ParseMode
from aiogram.filters import StateFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData

router = Router(name="events")
router.message.filter(UserVerified(verified=True))
router.callback_query.filter(UserVerified(verified=True))

# 1 GB — practical limit per file
_MAX_FILE_BYTES = 1024 * 1024 * 1024


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


# ── Callback data ──────────────────────────────────────────────────────────────

class SelectEvent(CallbackData, prefix="sel_ev"):
    event_id: str


class StartUpload(CallbackData, prefix="st_upl"):
    event_id: str


class ListMyFiles(CallbackData, prefix="lst_mf"):
    event_id: str


class FileAction(CallbackData, prefix="f_act"):
    file_id: str


class ToggleFile(CallbackData, prefix="tgl_f"):
    file_id: str


# ── FSM ────────────────────────────────────────────────────────────────────────

class UploadStates(StatesGroup):
    waiting_file = State()


# ── Helpers ────────────────────────────────────────────────────────────────────

def _type_icon(ft: FileType) -> str:
    return {"IMAGE": "🖼", "VIDEO": "🎬", "FILE": "📄"}.get(ft.value, "📎")


# ── Handlers ──────────────────────────────────────────────────────────────────

@router.callback_query(OpenEvents.filter(), StateFilter(None))
async def list_events(callback: CallbackQuery, container: Container) -> None:
    events = await container.event_service.get_all()
    if not events:
        await callback.answer("No events available yet.", show_alert=True)
        return

    events_sorted = sorted(events, key=lambda e: e.date, reverse=True)
    builder = InlineKeyboardBuilder()
    for ev in events_sorted:
        builder.row(InlineKeyboardButton(
            text=f"{ev.name} — {ev.date.strftime('%d.%m.%Y')} ({ev.photos_count} 📎)",
            callback_data=SelectEvent(event_id=ev.id).pack(),
        ))
    builder.row(InlineKeyboardButton(text="« Back", callback_data=OpenMenu().pack()))
    await callback.message.edit_text("📋 Select an event:", reply_markup=builder.as_markup())


@router.callback_query(SelectEvent.filter(), StateFilter(None))
async def show_event(callback: CallbackQuery, callback_data: SelectEvent,
                     container: Container) -> None:
    ev = await container.event_service.get_by_id(callback_data.event_id)
    if not ev:
        await callback.answer("Event not found.", show_alert=True)
        return

    raw_id = ev.id.replace("-", "")
    slug = raw_id[:4] + raw_id[-8:]
    webapp_url = container.settings.webapp_base_url
    event_url = f"{webapp_url}/{slug}" if webapp_url else None

    text = f"📅 {ev.name}\nDate: {ev.date.strftime('%d.%m.%Y')}\nFiles: {ev.photos_count}"

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="📤 Upload file",
        callback_data=StartUpload(event_id=ev.id).pack(),
    ))
    builder.row(InlineKeyboardButton(
        text="📋 My files",
        callback_data=ListMyFiles(event_id=ev.id).pack(),
    ))
    if event_url:
        builder.row(InlineKeyboardButton(text="🌐 View gallery", url=event_url))
    builder.row(InlineKeyboardButton(text="« Back", callback_data=OpenEvents().pack()))
    await callback.message.edit_text(text, reply_markup=builder.as_markup())


# ── Upload ─────────────────────────────────────────────────────────────────────

@router.callback_query(StartUpload.filter(), StateFilter(None))
async def prompt_upload(callback: CallbackQuery, callback_data: StartUpload,
                        state: FSMContext) -> None:
    await state.set_state(UploadStates.waiting_file)
    await state.update_data(event_id=callback_data.event_id)

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✅ Done", callback_data=OpenMenu().pack()))
    builder.row(InlineKeyboardButton(
        text="« Back",
        callback_data=SelectEvent(event_id=callback_data.event_id).pack(),
    ))
    await callback.message.edit_text(
        "📎 Send your file(s) now — photos, videos, documents and more are accepted.\n\n"
        "Files are visible to everyone by default — you can hide them via 📋 My files.\n\n"
        "Press Done when finished.",
        reply_markup=builder.as_markup(),
    )


@router.message(
    StateFilter(UploadStates.waiting_file),
    F.photo | F.document | F.video | F.animation | F.audio | F.voice,
)
async def receive_file(message: Message, state: FSMContext,
                       container: Container, bot: Bot, user: User) -> None:
    info = _extract_file_info(message)
    if not info:
        await message.reply("Unsupported file type.")
        return

    tg_file_id, original_name, file_size = info

    if file_size > _MAX_FILE_BYTES:
        await message.reply(
            f"⚠️ File is too large ({file_size // (1024*1024)} MB). Max 1 GB per file."
        )
        return

    data = await state.get_data()
    event_id = data["event_id"]
    ev = await container.event_service.get_by_id(event_id)
    if not ev:
        await message.reply("Event not found. Use /start to restart.")
        await state.clear()
        return

    # Download from Telegram (or read directly from disk when using local Bot API server)
    tg_file = await bot.get_file(tg_file_id)
    abs_path = tg_file.file_path  # absolute on local server, relative on official servers
    local_root = container.settings.botapi_local_files_path  # /var/lib/telegram-bot-api

    if abs_path and abs_path.startswith("/"):
        # Local Bot API: read directly from disk via the configured local root.
        # On host (dev): BOTAPI_LOCAL_FILES_PATH=./data/botapi so /var/lib/.../f.jpg → ./data/botapi/.../f.jpg
        relative = abs_path.removeprefix("/var/lib/telegram-bot-api/")
        local_path = Path(local_root) / relative
        file_data = await asyncio.to_thread(local_path.read_bytes)
    else:
        buf = io.BytesIO()
        await bot.download_file(abs_path, buf)
        file_data = buf.getvalue()

    file_type = _detect_type(original_name)
    content_type = _content_type(original_name)

    # Use a unique filename in S3, preserve extension
    ext = original_name.rsplit(".", 1)[-1] if "." in original_name else "bin"
    s3_filename = f"{uuid.uuid4()}.{ext}"

    await container.s3_client.upload(
        folder=ev.images_folder,
        filename=s3_filename,
        data=file_data,
        content_type=content_type,
    )

    await container.media_file_service.create(
        file_name=s3_filename,
        event_id=event_id,
        author_id=user.id,
        file_type=file_type,
    )
    await container.event_service.increment_photos_count(event_id)

    # Delete the local botapi cache file to free disk space
    if abs_path and abs_path.startswith("/"):
        relative = abs_path.removeprefix("/var/lib/telegram-bot-api/")
        local_path = Path(container.settings.botapi_local_files_path) / relative
        await asyncio.to_thread(lambda: os.unlink(local_path) if local_path.exists() else None)

    await message.reply(
        f"✅ {_type_icon(file_type)} File uploaded!\n"
        "It's visible to everyone by default.\n"
        "You can hide it anytime via 📋 My files."
    )


@router.message(StateFilter(UploadStates.waiting_file), Command("done"))
async def done_upload(message: Message, state: FSMContext,
                      container: Container, user: User) -> None:
    await state.clear()
    await message.answer(
        "✅ Upload session ended.",
        reply_markup=_menu_keyboard(user.is_verified, container.settings.webapp_base_url),
    )


@router.callback_query(OpenMenu.filter(), StateFilter(UploadStates.waiting_file))
async def done_upload_cb(callback: CallbackQuery, state: FSMContext,
                         container: Container, user: User) -> None:
    await state.clear()
    await callback.message.edit_text(
        "👋 Welcome back to Memory Archive!",
        reply_markup=_menu_keyboard(user.is_verified, container.settings.webapp_base_url),
    )


# ── My files ──────────────────────────────────────────────────────────────────

@router.callback_query(ListMyFiles.filter(), StateFilter(None))
async def list_my_files(callback: CallbackQuery, callback_data: ListMyFiles,
                        container: Container, user: User) -> None:
    files = await container.media_file_service.get_by_author_and_event(
        author_id=user.id, event_id=callback_data.event_id
    )

    if not files:
        await callback.answer("You haven't uploaded any files to this event yet.",
                              show_alert=True)
        return

    builder = InlineKeyboardBuilder()
    for i, f in enumerate(files, 1):
        vis = "✅" if f.is_showed else "🙈"
        label = f"{i}. {_type_icon(f.type)} {f.file_name[:28]} {vis}"
        builder.row(InlineKeyboardButton(
            text=label,
            callback_data=FileAction(file_id=f.id).pack(),
        ))
    builder.row(InlineKeyboardButton(
        text="« Back",
        callback_data=SelectEvent(event_id=callback_data.event_id).pack(),
    ))
    await callback.message.edit_text("📋 Your files for this event:", reply_markup=builder.as_markup())


@router.callback_query(FileAction.filter(), StateFilter(None))
async def file_detail(callback: CallbackQuery, callback_data: FileAction,
                      container: Container) -> None:
    f = await container.media_file_service.get_by_id(callback_data.file_id)
    if not f:
        await callback.answer("File not found.", show_alert=True)
        return

    ev = await container.event_service.get_by_id(f.event_id)
    if not ev:
        await callback.answer("Event not found.", show_alert=True)
        return

    s3_key = f"{ev.images_folder}/{f.file_name}"
    presigned = await container.s3_client.presigned_url(s3_key, expires_seconds=86400)

    vis_label = "visible ✅" if f.is_showed else "hidden 🙈"
    toggle_label = "🙈 Hide" if f.is_showed else "👁 Show"

    text = (
        f"{_type_icon(f.type)} <b>{f.file_name}</b>\n"
        f"Type: {f.type.value}\n"
        f"Status: {vis_label}\n\n"
        f'<a href="{presigned}">🔗 Open file (link valid 24 h)</a>'
    )

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text=toggle_label,
        callback_data=ToggleFile(file_id=f.id).pack(),
    ))
    builder.row(InlineKeyboardButton(
        text="« Back",
        callback_data=ListMyFiles(event_id=f.event_id).pack(),
    ))
    await callback.message.edit_text(text, reply_markup=builder.as_markup(),
                                     parse_mode=ParseMode.HTML)


@router.callback_query(ToggleFile.filter(), StateFilter(None))
async def toggle_file(callback: CallbackQuery, callback_data: ToggleFile,
                      container: Container) -> None:
    f = await container.media_file_service.get_by_id(callback_data.file_id)
    if not f:
        await callback.answer("File not found.", show_alert=True)
        return

    new_state = not f.is_showed
    await container.media_file_service.set_showed(f.id, new_state)

    action = "visible ✅" if new_state else "hidden 🙈"
    await callback.answer(f"File is now {action}", show_alert=False)

    # Refresh detail view
    ev = await container.event_service.get_by_id(f.event_id)
    s3_key = f"{ev.images_folder}/{f.file_name}"
    presigned = await container.s3_client.presigned_url(s3_key, expires_seconds=86400)

    toggle_label = "🙈 Hide" if new_state else "👁 Show"
    text = (
        f"{_type_icon(f.type)} <b>{f.file_name}</b>\n"
        f"Type: {f.type.value}\n"
        f"Status: {action}\n\n"
        f'<a href="{presigned}">🔗 Open file (link valid 24 h)</a>'
    )

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text=toggle_label,
        callback_data=ToggleFile(file_id=f.id).pack(),
    ))
    builder.row(InlineKeyboardButton(
        text="« Back",
        callback_data=ListMyFiles(event_id=f.event_id).pack(),
    ))
    await callback.message.edit_text(text, reply_markup=builder.as_markup(),
                                     parse_mode=ParseMode.HTML)
