from app.bot.routers.default.router import router

from aiogram.filters import StateFilter, Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext


@router.message(StateFilter(None), Command(commands=["cancel"]))
async def cancel_nothing(message: Message) -> None:
    await message.reply("Nothing to cancel, but.. okay?\n\nCanceled successfully!")


@router.message(StateFilter("*"), Command(commands=["cancel"]))
async def cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.reply("Canceled successfully!")
