from app.bootstrap import Container
from app.domain.user import User
from app.bot.filters.user_verified import UserVerified
from app.bot.routers.user.menu import StartVerify, _menu_keyboard

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData

router = Router(name="verify")


class VerifyStates(StatesGroup):
    login = State()
    password = State()


class CancelVerify(CallbackData, prefix="cancel_verify"):
    pass


def _cancel_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="❌ Cancel", callback_data=CancelVerify().pack()
    ))
    return builder.as_markup()


@router.callback_query(StateFilter(None), StartVerify.filter(), UserVerified(verified=False))
async def start_verify(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(VerifyStates.login)
    await callback.message.edit_text(
        "🔐 Enter your EMIS login (student ID number):",
        reply_markup=_cancel_keyboard(),
    )


@router.callback_query(CancelVerify.filter(), StateFilter(VerifyStates.login, VerifyStates.password))
async def cancel_verify(callback: CallbackQuery, state: FSMContext,
                        container: Container, user: User) -> None:
    await state.clear()
    webapp_url = container.settings.webapp_base_url
    await callback.message.edit_text(
        "Verification cancelled.",
        reply_markup=_menu_keyboard(user.is_verified, webapp_url),
    )


@router.message(StateFilter(VerifyStates.login), F.text)
async def receive_login(message: Message, state: FSMContext) -> None:
    await state.update_data(emis_login=message.text.strip())
    await state.set_state(VerifyStates.password)
    await message.answer(
        "🔑 Now enter your EMIS password:\n\n"
        "⚠️ Your password is used one-time only for verification and is never stored.",
        reply_markup=_cancel_keyboard(),
    )


@router.message(StateFilter(VerifyStates.password), F.text)
async def receive_password(message: Message, state: FSMContext,
                           container: Container, user: User) -> None:
    data = await state.get_data()
    login = data.get("emis_login", "")
    password = message.text.strip()

    # Delete the password message immediately to avoid it sitting in chat
    try:
        await message.delete()
    except Exception:
        pass

    await message.answer("⏳ Verifying your account...")

    from app.infrastructure.emis.exceptions import EMISAuthError, EMISRequestError

    try:
        token = await container.emis_client.login(login, password)
        curriculum = await container.emis_client.get_curriculum(token)
    except EMISAuthError:
        await message.answer(
            "❌ Invalid login or password. Please try /start and verify again."
        )
        await state.clear()
        return
    except EMISRequestError as e:
        await message.answer(f"❌ EMIS error: {e.description}. Try again later.")
        await state.clear()
        return

    institution_id = curriculum.get("institution_id")
    if institution_id != container.settings.emis_institution_id:
        await message.answer(
            "❌ This bot is for IHD (International House Tashkent) students only.\n"
            "Your institution is not recognized."
        )
        await state.clear()
        return

    await container.user_service.verify(telegram_id=message.from_user.id)
    await state.clear()

    # Refresh user object for correct keyboard
    verified_user = await container.user_service.get_by_telegram_id(message.from_user.id)
    webapp_url = container.settings.webapp_base_url

    await message.answer(
        "✅ Verification successful! Welcome to Memory Archive.\n\n"
        "You can now upload photos to events.",
        reply_markup=_menu_keyboard(verified_user.is_verified, webapp_url),
    )
