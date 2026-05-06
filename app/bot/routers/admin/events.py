import uuid
from datetime import datetime

from app.bootstrap import Container
from app.bot.routers.admin.router import router

from aiogram.filters import Command, CommandObject
from aiogram.types import Message


@router.message(Command("create_event"))
async def create_event(message: Message, command: CommandObject, container: Container) -> None:
    """Create a new event. Usage: /create_event <name> | <YYYY-MM-DD>"""
    args = command.args or ""
    if "|" not in args:
        await message.reply("Usage: /create_event <name> | <YYYY-MM-DD>")
        return

    parts = args.split("|", maxsplit=1)
    name = parts[0].strip()
    date_str = parts[1].strip()

    try:
        date = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        await message.reply("Invalid date format. Use YYYY-MM-DD.")
        return

    images_folder = str(uuid.uuid4())
    event = await container.event_service.create(
        name=name, date=date, images_folder=images_folder
    )

    raw_id = event.id.replace("-", "")
    slug = raw_id[:4] + raw_id[-8:]

    await message.reply(
        f"✅ Event created!\n"
        f"Name: {event.name}\n"
        f"Date: {event.date.strftime('%d.%m.%Y')}\n"
        f"ID: {event.id}\n"
        f"Slug: {slug}\n"
        f"S3 folder: {event.images_folder}"
    )
