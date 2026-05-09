from app.bootstrap import Container
from app.bot.routers.user.events.callbacks import FileAction, ListMyFiles, ToggleFile
from app.bot.routers.user.events.keyboards.events import file_detail_kb, my_files_list_kb
from app.bot.routers.user.events.router import router
from app.domain.file_type import FileType
from app.domain.user import User

from aiogram.enums import ParseMode
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery


def _type_icon(ft: FileType) -> str:
    return {"IMAGE": "🖼", "VIDEO": "🎬", "FILE": "📄"}.get(ft.value, "📎")


def _display_name(file_name: str, original_name: str | None) -> str:
    return original_name or file_name


@router.callback_query(ListMyFiles.filter(), StateFilter(None))
async def list_my_files(
    callback: CallbackQuery, callback_data: ListMyFiles, container: Container, user: User,
) -> None:
    files = await container.media_file_service.get_by_author_and_event(
        author_id=user.id, event_id=callback_data.event_id
    )
    if not files:
        await callback.answer("You haven't uploaded any files to this event yet.", show_alert=True)
        return
    await callback.message.edit_text(
        "📋 Your files for this event:",
        reply_markup=my_files_list_kb(files, callback_data.event_id),
    )


@router.callback_query(FileAction.filter(), StateFilter(None))
async def file_detail(
    callback: CallbackQuery, callback_data: FileAction, container: Container,
) -> None:
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
    display = _display_name(f.file_name, f.original_name)
    vis_label = "visible ✅" if f.is_showed else "hidden 🙈"

    text = (
        f"{_type_icon(f.type)} <b>{display}</b>\n"
        f"Type: {f.type.value}\n"
        f"Status: {vis_label}\n\n"
        f'<a href="{presigned}">🔗 Open file (link valid 24 h)</a>'
    )
    await callback.message.edit_text(
        text,
        reply_markup=file_detail_kb(f.id, f.event_id, f.is_showed),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(ToggleFile.filter(), StateFilter(None))
async def toggle_file(
    callback: CallbackQuery, callback_data: ToggleFile, container: Container,
) -> None:
    f = await container.media_file_service.get_by_id(callback_data.file_id)
    if not f:
        await callback.answer("File not found.", show_alert=True)
        return

    new_showed = not f.is_showed
    await container.media_file_service.set_showed(f.id, new_showed)
    action = "visible ✅" if new_showed else "hidden 🙈"
    await callback.answer(f"File is now {action}", show_alert=False)

    ev = await container.event_service.get_by_id(f.event_id)
    s3_key = f"{ev.images_folder}/{f.file_name}"
    presigned = await container.s3_client.presigned_url(s3_key, expires_seconds=86400)
    display = _display_name(f.file_name, f.original_name)

    text = (
        f"{_type_icon(f.type)} <b>{display}</b>\n"
        f"Type: {f.type.value}\n"
        f"Status: {action}\n\n"
        f'<a href="{presigned}">🔗 Open file (link valid 24 h)</a>'
    )
    await callback.message.edit_text(
        text,
        reply_markup=file_detail_kb(f.id, f.event_id, new_showed),
        parse_mode=ParseMode.HTML,
    )
