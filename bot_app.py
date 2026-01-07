import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from keyboards import post_keyboard


from premium_store import load_premium, save_premium
from draft_store import load_drafts, save_drafts, new_draft_id
from digest_builder import build_daily_digest

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "")
PRO_CHANNEL_ID = int(os.getenv("PRO_CHANNEL_ID", "0"))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

class PostFlow(StatesGroup):
    target = State()   # FREE або PRO
    text = State()     # текст поста
    source = State()   # лінк джерела (опційно)


def is_admin(message_or_user) -> bool:
    username = None

    # message
    if hasattr(message_or_user, "from_user") and message_or_user.from_user:
        username = message_or_user.from_user.username

    # user
    elif hasattr(message_or_user, "username"):
        username = message_or_user.username

    if not username or not ADMIN_USERNAME:
        return False

    return ("@" + username).lower() == ADMIN_USERNAME.lower()


def target_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="FREE"), KeyboardButton(text="PRO")],
            [KeyboardButton(text="Cancel")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

@dp.message(Command("post"))
async def post_start(message: types.Message, state: FSMContext):
    if not is_admin(message):
        await message.answer("❌ Access denied")
        return

    await state.clear()
    await state.set_state(PostFlow.target)
    await message.answer(
        "Куди постити? Вибери FREE або PRO.",
        reply_markup=target_keyboard()
    )

@dp.message(PostFlow.target)
async def post_choose_target(message: types.Message, state: FSMContext):
    choice = (message.text or "").strip().upper()

    if choice == "CANCEL":
        await state.clear()
        await message.answer("OK, cancelled.", reply_markup=ReplyKeyboardRemove())
        return

    if choice not in ("FREE", "PRO"):
        await message.answer("Вибери кнопкою: FREE або PRO (або Cancel).")
        return

    await state.update_data(target=choice)
    await state.set_state(PostFlow.text)
    await message.answer(
        "Надішли текст поста (можна з емодзі, UA/EN).",
        reply_markup=ReplyKeyboardRemove()
    )

@dp.message(PostFlow.text)
async def post_get_text(message: types.Message, state: FSMContext):
    text = (message.text or "").strip()
    if len(text) < 3:
        await message.answer("Текст занадто короткий. Надішли нормальний текст поста.")
        return

    await state.update_data(text=text)
    await state.set_state(PostFlow.source)
    await message.answer(
        "Тепер надішли лінк джерела (https://...), або напиши `skip` якщо без джерела."
    )

@dp.message(PostFlow.source)
async def post_get_source_and_publish(message: types.Message, state: FSMContext):
    data = await state.get_data()
    target = data["target"]
    text = data["text"]

    source = (message.text or "").strip()
    if source.lower() == "skip":
        source = None

    # Визначаємо куди постити
    if target == "FREE":
        channel_id = os.getenv("CHANNEL_ID")
        if not channel_id:
            await message.answer("❌ CHANNEL_ID not set in .env")
            await state.clear()
            return
    else:
        channel_id = int(os.getenv("PRO_CHANNEL_ID", "0"))
        if channel_id == 0:
            await message.answer("❌ PRO_CHANNEL_ID not set in .env")
            await state.clear()
            return

    try:
        await bot.send_message(
            chat_id=channel_id,
            text=text,
            reply_markup=post_keyboard(source),
            disable_web_page_preview=False
        )
        await message.answer(f"✅ Posted to {target}.")
    except Exception as e:
        await message.answer(f"❌ Post failed: {e}")

    await state.clear()

def premium_request_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ Request Premium", callback_data="get_premium")]
    ])

def draft_keyboard(draft_id: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Approve & Post to PRO", callback_data=f"approve:{draft_id}"),
            InlineKeyboardButton(text="❌ Reject", callback_data=f"reject:{draft_id}")
        ]
    ])

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    premium_users = load_premium()
    if message.from_user.id in premium_users:
        await message.answer(
            "✅ You have PRO access.\nUse /pro to get the latest PRO digest.",
        )
    else:
        text = (
            "🧠 HelloWorld Intel\n\n"
            "UA/EN digest on Crypto, AI/Tech and SAP (enterprise).\n\n"
            "⭐ PRO includes:\n"
            "• Filtered daily digest\n"
            "• Enterprise AI / SAP focus\n"
            "• Crypto regulation & macro\n\n"
            "Price: $9 / month\n"
            "Tap below to request access."
        )
        await message.answer(text, reply_markup=premium_request_keyboard())

@dp.callback_query(lambda c: c.data == "get_premium")
async def premium_request(callback: types.CallbackQuery):
    await callback.message.answer(
        "⭐ Premium access request\n\n"
        f"Please contact admin to activate access:\n{ADMIN_USERNAME}\n\n"
        "After confirmation you will be added to PRO."
    )
    await callback.answer()

# -------- PREMIUM-ONLY CONTENT --------

@dp.message(Command("pro"))
async def pro_handler(message: types.Message):
    premium_users = load_premium()
    if message.from_user.id not in premium_users:
        await message.answer(
            "⭐ PRO content is available for Premium users only.\n"
            f"Request access: {ADMIN_USERNAME}\n"
            "After activation, use /pro again."
        )
        return

    # Premium user: show last approved digest if exists
    drafts = load_drafts()
    last = drafts.get("_last_posted_text")
    if last:
        await message.answer(last)
    else:
        await message.answer("PRO digest is not published yet. Please check later today.")

# -------- ADMIN: GRANT PREMIUM --------

@dp.message(Command("grant"))
async def grant_premium(message: types.Message):
    if not is_admin(message):
        await message.answer("❌ Access denied")
        return

    parts = message.text.split()
    if len(parts) != 2:
        await message.answer("Usage: /grant <user_id>\nTip: forward me a user's message to see their id.")
        return

    try:
        uid = int(parts[1])
    except ValueError:
        await message.answer("❌ user_id must be a number.")
        return

    premium_users = load_premium()
    premium_users.add(uid)
    save_premium(premium_users)
    await message.answer(f"✅ user_id {uid} granted PRO access.\nThey can now use /pro.")

# -------- ADMIN: SEND DRAFT TO ADMIN --------

@dp.message(Command("draft"))
async def send_draft(message: types.Message):
    if not is_admin(message):
        await message.answer("❌ Access denied")
        return

    if PRO_CHANNEL_ID == 0:
        await message.answer("❌ PRO_CHANNEL_ID is not set in .env")
        return

    draft_text = build_daily_digest()
    d_id = new_draft_id()

    drafts = load_drafts()
    drafts[d_id] = {"text": draft_text}
    save_drafts(drafts)

    await message.answer(draft_text, reply_markup=draft_keyboard(d_id))

# -------- ADMIN: APPROVE / REJECT --------

@dp.callback_query(lambda c: c.data and (c.data.startswith("approve:") or c.data.startswith("reject:")))
async def draft_action(callback: types.CallbackQuery):
    if not is_admin(callback.from_user):
        await callback.answer("Access denied", show_alert=True)
        return

    action, draft_id = callback.data.split(":", 1)
    drafts = load_drafts()
    draft = drafts.get(draft_id)

    if not draft:
        await callback.answer("Draft not found", show_alert=True)
        return

    if action == "reject":
        drafts.pop(draft_id, None)
        save_drafts(drafts)
        await callback.message.edit_text("❌ Draft rejected.")
        await callback.answer()
        return

    # approve -> post to PRO channel
    text = draft["text"]

    try:
        await bot.send_message(chat_id=PRO_CHANNEL_ID, text=text, disable_web_page_preview=True)
        drafts["_last_posted_text"] = text
        drafts.pop(draft_id, None)
        save_drafts(drafts)
        await callback.message.edit_text("✅ Posted to PRO channel.")
        await callback.answer()
    except Exception as e:
        await callback.answer(f"Post failed: {e}", show_alert=True)

if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))
