from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Optional

def post_keyboard(source_url: Optional[str] = None) -> InlineKeyboardMarkup:
    row1 = []
    if source_url:
        row1.append(InlineKeyboardButton(text="🔗 Джерело", url=source_url))

    # Обговорення (поки веде в твій free-канал; потім зробимо окремий чат)
    row1.append(InlineKeyboardButton(text="💬 Обговорити", url="https://t.me/helloworld_intel"))

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        row1,
        [InlineKeyboardButton(text="⭐ Premium", url="https://t.me/hello_world_intel_bot")]
    ])
    return keyboard
