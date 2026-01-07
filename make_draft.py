import os
import asyncio
from dotenv import load_dotenv

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from digest_builder import build_daily_digest
from draft_store import load_drafts, save_drafts, new_draft_id

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))

def draft_keyboard(draft_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Approve & Post to PRO", callback_data=f"approve:{draft_id}"),
            InlineKeyboardButton(text="❌ Reject", callback_data=f"reject:{draft_id}")
        ]
    ])

async def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN not set in .env")
    if ADMIN_USER_ID == 0:
        raise RuntimeError("ADMIN_USER_ID not set in .env")

    bot = Bot(token=BOT_TOKEN)

    draft_text = build_daily_digest()
    d_id = new_draft_id()

    # зберігаємо чернетку, щоб кнопка Approve працювала через bot_app.py
    drafts = load_drafts()
    drafts[d_id] = {"text": draft_text}
    save_drafts(drafts)

    await bot.send_message(
        chat_id=ADMIN_USER_ID,
        text=draft_text,
        reply_markup=draft_keyboard(d_id),
        disable_web_page_preview=True
    )

    await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
