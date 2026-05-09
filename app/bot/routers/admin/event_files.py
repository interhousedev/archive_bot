from app.bootstrap import Container
from app.bot.routers.admin.callbacks import (
    ManageEventFiles,
    ManageFileDelete,
    ManageFileDeleteConfirm,
    ManageFileDetail,
    ManageFileToggleBan,
)
from app.bot.routers.admin.keyboards.events import (
    _PAGE_SIZE,
    event_detail_kb,
    event_files_kb,
    file_action_kb,
    file_delete_confirm_kb,
)
from app.bot.routers.admin.router import router
from app.domain.file_type import FileType

from aiogram.enums import ParseMode
from aiogram.types import CallbackQuery


def _type_icon(ft: FileType) -> str:
    return {"IMAGE": "🖼", "VIDEO": "🎬", "FILE": "📄"}.get(ft.value, "📎")


def _file_detail_text(f, gallery_status: str, user_status: str) -> str:
    display = f.original_name or f.file_name
    return (
        f"{_type_icon(f.type)} <b>{display}</b>\n"
        f"Type: {f.type.value}\n"
        f"Gallery: {gallery_status}\n"
        f"Uploader: {user_status}"
    )


@router.callback_query(ManageEventFiles.filter())
async def show_event_files(
    callback: CallbackQuery, callback_data: ManageEventFiles, container: Container,
) -> None:
    ev = await container.event_service.get_by_id(callback_data.event_id)
    if not ev:
        await callback.answer("Event not found.", show_alert=True)
        return

    files = await container.media_file_service.get_all_for_event(callback_data.event_id)
    if not files:
        await callback.answer("No files in this event.", show_alert=True)
        return

    page = callback_data.page
    await callback.message.edit_text(
        f"📁 {ev.name} — {len(files)} file(s) — page {page + 1}:",
        reply_markup=event_files_kb(files, callback_data.event_id, page),
    )


@router.callback_query(ManageFileDetail.filter())
async def show_file_detail(
    callback: CallbackQuery, callback_data: ManageFileDetail, container: Container,
) -> None:
    f = await container.media_file_service.get_by_id(callback_data.file_id)
    if not f:
        await callback.answer("File not found.", show_alert=True)
        return

    ev = await container.event_service.get_by_id(f.event_id)
    s3_key = f"{ev.images_folder}/{f.file_name}"
    presigned = await container.s3_client.presigned_url(s3_key, expires_seconds=7 * 86400)

    gallery_status = "🚫 Hidden" if f.is_banned else "✅ Visible"
    user_status = "✅ Shown" if f.is_showed else "🙈 Hidden by uploader"

    await callback.message.edit_text(
        _file_detail_text(f, gallery_status, user_status),
        reply_markup=file_action_kb(f, callback_data.page, presigned),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(ManageFileToggleBan.filter())
async def toggle_file_ban(
    callback: CallbackQuery, callback_data: ManageFileToggleBan, container: Container,
) -> None:
    f = await container.media_file_service.get_by_id(callback_data.file_id)
    if not f:
        await callback.answer("File not found.", show_alert=True)
        return

    new_banned = not f.is_banned
    await container.media_file_service.set_banned(f.id, new_banned)

    ev = await container.event_service.get_by_id(f.event_id)
    s3_key = f"{ev.images_folder}/{f.file_name}"
    presigned = await container.s3_client.presigned_url(s3_key, expires_seconds=7 * 86400)

    f_updated = await container.media_file_service.get_by_id(f.id)
    gallery_status = "🚫 Hidden" if new_banned else "✅ Visible"
    user_status = "✅ Shown" if f.is_showed else "🙈 Hidden by uploader"

    await callback.message.edit_text(
        _file_detail_text(f_updated, gallery_status, user_status),
        reply_markup=file_action_kb(f_updated, callback_data.page, presigned),
        parse_mode=ParseMode.HTML,
    )
    await callback.answer("Hidden from gallery." if new_banned else "Visible in gallery.")


@router.callback_query(ManageFileDelete.filter())
async def confirm_file_delete(
    callback: CallbackQuery, callback_data: ManageFileDelete, container: Container,
) -> None:
    f = await container.media_file_service.get_by_id(callback_data.file_id)
    if not f:
        await callback.answer("File not found.", show_alert=True)
        return

    display = f.original_name or f.file_name
    await callback.message.edit_text(
        f"🗑 Delete <b>{display}</b>?\nThis removes it from S3 and the database permanently.",
        reply_markup=file_delete_confirm_kb(callback_data.file_id, callback_data.page),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(ManageFileDeleteConfirm.filter())
async def do_file_delete(
    callback: CallbackQuery, callback_data: ManageFileDeleteConfirm, container: Container,
) -> None:
    f = await container.media_file_service.get_by_id(callback_data.file_id)
    if not f:
        await callback.answer("File already deleted.", show_alert=True)
        return

    ev = await container.event_service.get_by_id(f.event_id)
    await container.s3_client.delete(f"{ev.images_folder}/{f.file_name}")
    await container.media_file_service.delete(f.id)
    await container.event_service.decrement_photos_count(ev.id)

    files = await container.media_file_service.get_all_for_event(ev.id)
    await callback.answer("File deleted.")

    if not files:
        ev_updated = await container.event_service.get_by_id(ev.id)
        from app.bot.routers.admin.manage_events import _event_detail_text
        await callback.message.edit_text(
            "✅ File deleted. No files remaining.\n\n" + _event_detail_text(ev_updated),
            reply_markup=event_detail_kb(ev.id, 0),
        )
        return

    total_pages = max(1, (len(files) + _PAGE_SIZE - 1) // _PAGE_SIZE)
    page = min(callback_data.page, total_pages - 1)
    await callback.message.edit_text(
        f"✅ File deleted.\n\n📁 {ev.name} — {len(files)} file(s) — page {page + 1}:",
        reply_markup=event_files_kb(files, ev.id, page),
    )