from app.bootstrap import Container
from app.bot.routers.admin.callbacks import AdminBanFile, AdminNoop, AdminToggleSender, \
    AdminUnbanFile
from app.bot.routers.admin.keyboards.moderation import admin_notification_kb
from app.bot.routers.admin.router import router

from aiogram import Bot
from aiogram.types import CallbackQuery, InlineKeyboardMarkup


async def _edit_notification(message, text: str, kb: InlineKeyboardMarkup) -> None:
    if message.photo:
        await message.edit_caption(caption=text, reply_markup=kb)
    else:
        await message.edit_text(text=text, reply_markup=kb)


@router.callback_query(AdminNoop.filter())
async def admin_noop(callback: CallbackQuery) -> None:
    await callback.answer()


@router.callback_query(AdminBanFile.filter())
async def admin_ban_file(
    callback: CallbackQuery, callback_data: AdminBanFile, container: Container,
) -> None:
    f = await container.media_file_service.get_by_id(callback_data.file_id)
    if not f:
        await callback.answer("File not found.", show_alert=True)
        return

    await container.media_file_service.set_banned(f.id, True)

    ev = await container.event_service.get_by_id(f.event_id)
    s3_key = f"{ev.images_folder}/{f.file_name}"
    presigned = await container.s3_client.presigned_url(s3_key, expires_seconds=7 * 86400)

    user = await container.user_service.get_by_telegram_id(callback_data.author_telegram_id)
    sender_banned = user.is_banned if user else False

    kb = admin_notification_kb(
        file_id=f.id,
        author_telegram_id=callback_data.author_telegram_id,
        file_banned=True,
        sender_banned=sender_banned,
        presigned_url=presigned,
    )
    original_text = callback.message.caption or callback.message.text or ""
    await _edit_notification(callback.message, original_text, kb)
    await callback.answer("File hidden.")

@router.callback_query(AdminUnbanFile.filter())
async def admin_unban_file(
    callback: CallbackQuery, callback_data: AdminUnbanFile, container: Container,
) -> None:
    f = await container.media_file_service.get_by_id(callback_data.file_id)
    if not f:
        await callback.answer("File not found.", show_alert=True)
        return

    await container.media_file_service.set_banned(f.id, False)

    ev = await container.event_service.get_by_id(f.event_id)
    s3_key = f"{ev.images_folder}/{f.file_name}"
    presigned = await container.s3_client.presigned_url(s3_key, expires_seconds=7 * 86400)

    user = await container.user_service.get_by_telegram_id(callback_data.author_telegram_id)
    sender_banned = user.is_banned if user else False

    kb = admin_notification_kb(
        file_id=f.id,
        author_telegram_id=callback_data.author_telegram_id,
        file_banned=False,
        sender_banned=sender_banned,
        presigned_url=presigned,
    )
    original_text = callback.message.caption or callback.message.text or ""
    await _edit_notification(callback.message, original_text, kb)
    await callback.answer("File unhidden.")


@router.callback_query(AdminToggleSender.filter())
async def admin_toggle_sender(
    callback: CallbackQuery,
    callback_data: AdminToggleSender,
    container: Container,
    bot: Bot,
) -> None:
    user = await container.user_service.get_by_telegram_id(callback_data.author_telegram_id)
    if not user:
        await callback.answer("User not found.", show_alert=True)
        return

    new_banned = not user.is_banned
    await container.user_service.set_banned(callback_data.author_telegram_id, new_banned)

    if new_banned:
        admin_label = f"@{callback.from_user.username}" if callback.from_user.username else "an admin"
        try:
            await bot.send_message(
                callback_data.author_telegram_id,
                f"🚫 You have been restricted from uploading by {admin_label}.",
            )
        except Exception:
            pass

    f = await container.media_file_service.get_by_id(callback_data.file_id)
    ev = await container.event_service.get_by_id(f.event_id)
    s3_key = f"{ev.images_folder}/{f.file_name}"
    presigned = await container.s3_client.presigned_url(s3_key, expires_seconds=7 * 86400)

    kb = admin_notification_kb(
        file_id=f.id,
        author_telegram_id=callback_data.author_telegram_id,
        file_banned=f.is_banned,
        sender_banned=new_banned,
        presigned_url=presigned,
    )
    original_text = callback.message.caption or callback.message.text or ""
    await _edit_notification(callback.message, original_text, kb)
    await callback.answer("Sender banned." if new_banned else "Sender unbanned.")