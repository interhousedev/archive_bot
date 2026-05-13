from app.bootstrap import Container
from app.bot.routers.admin.router import router

from aiogram import Bot
from aiogram.filters import Command, CommandObject, StateFilter
from aiogram.types import Message


def _admin_label(message: Message) -> str:
    user = message.from_user
    if user.username:
        return f"@{user.username}"
    return user.full_name or str(user.id)


@router.message(Command("disapprove"), StateFilter(None))
async def disapprove_user(
    message: Message,
    command: CommandObject,
    container: Container,
    bot: Bot,
) -> None:
    raw = (command.args or "").strip()
    if not raw:
        await message.answer(
            "Usage: /disapprove <chat_id>\n\n"
            "Manually unverifies a student by their Telegram chat ID."
        )
        return

    try:
        target_id = int(raw.split()[0])
    except ValueError:
        await message.answer("❌ chat_id must be an integer.")
        return

    target = await container.user_service.get_by_telegram_id(target_id)
    if target is None:
        await message.answer(
            f"❌ No user with chat_id <code>{target_id}</code> has interacted with the bot yet.",
            parse_mode="HTML",
        )
        return

    if not target.is_verified:
        await message.answer(f"ℹ️ User <code>{target_id}</code> is not verified.", parse_mode="HTML")
        return

    await container.user_service.unverify(telegram_id=target_id)

    admin_label = _admin_label(message)

    await message.answer(
        f"✅ User <code>{target_id}</code> has been manually disapproved.",
        parse_mode="HTML",
    )

    try:
        await bot.send_message(
            target_id,
            "❌ You have been manually unverified by an admin.\n"
            "You can now upload photos to events. Send /start to open the menu.",
        )
    except Exception:
        pass

    notify_text = (
        f"🛡️ Manual disapproval\n"
        f"Admin: {admin_label} (<code>{message.from_user.id}</code>)\n"
        f"Disapproved user chat_id: <code>{target_id}</code>"
    )
    for admin_id in container.settings.admins_ids:
        if admin_id == message.from_user.id:
            continue
        try:
            await bot.send_message(admin_id, notify_text, parse_mode="HTML")
        except Exception:
            pass