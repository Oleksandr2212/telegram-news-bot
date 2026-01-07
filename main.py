import asyncio
import os
import feedparser
from dotenv import load_dotenv
from aiogram import Bot

from storage import load_posted, save_posted
from summarizer import format_post
from keyboards import post_keyboard

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

RSS_FEEDS = [
    # UA — 60%
    ("tech", "ua", "https://www.liga.net/ua/tech/technology/rss.xml"),
    ("tech", "ua", "https://www.liga.net/ua/tech/all/rss.xml"),
    ("economy", "ua", "https://www.epravda.com.ua/rss/"),

    # EN — 40%
    ("crypto", "en", "https://www.coindesk.com/arc/outboundfeeds/rss/"),
    ("sap", "en", "https://news.sap.com/feed/"),
]

def fetch_items(limit_per_feed=10):
    items = []
    for topic, lang, url in RSS_FEEDS:
        feed = feedparser.parse(url)
        for e in feed.entries[:limit_per_feed]:
            link = e.get("link", "")
            title = e.get("title", "")
            if link and title:
                items.append({"topic": topic, "lang": lang, "title": title, "link": link})
    return items

async def main():
    if not BOT_TOKEN or not CHANNEL_ID:
        raise RuntimeError("Missing BOT_TOKEN or CHANNEL_ID in .env")

    bot = Bot(token=BOT_TOKEN)
    posted = load_posted()

    items = fetch_items(limit_per_feed=10)

    posted_count = 0
    for it in items:
        if it["link"] in posted:
            continue

        text = format_post(
    title=it["title"],
    link=it["link"],
    topic=it["topic"],
    lang=it["lang"]
)
        await bot.send_message(
    chat_id=CHANNEL_ID,
    text=text,
    reply_markup=post_keyboard(it["link"]),
    disable_web_page_preview=False
)

        posted.add(it["link"])
        posted_count += 1

        save_posted(posted)
        await asyncio.sleep(2)

        if posted_count >= 8:  # щоб не спамити, максимум 8 за запуск
            break

    await bot.session.close()
    print(f"Posted: {posted_count} new items")

if __name__ == "__main__":
    asyncio.run(main())
