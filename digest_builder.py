import os
import feedparser
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# ---------- ENV ----------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
MAX_OUTPUT_TOKENS = int(os.getenv("OPENAI_MAX_OUTPUT_TOKENS", "900"))
MAX_ITEMS = int(os.getenv("OPENAI_MAX_ITEMS", "10"))

# ---------- RSS FEEDS ----------
RSS_FEEDS = [
    ("tech", "ua", "https://www.liga.net/ua/tech/technology/rss.xml"),
    ("economy", "ua", "https://www.epravda.com.ua/rss/"),
    ("crypto", "en", "https://www.coindesk.com/arc/outboundfeeds/rss/"),
    ("sap", "en", "https://news.sap.com/feed/"),
]

# ---------- FETCH ----------
def fetch_top_items():
    items = []
    for topic, lang, url in RSS_FEEDS:
        feed = feedparser.parse(url)
        for e in feed.entries[:5]:
            title = e.get("title", "").strip()
            link = e.get("link", "").strip()
            if title and link:
                items.append({
                    "topic": topic,
                    "lang": lang,
                    "title": title,
                    "link": link
                })
    return items[:MAX_ITEMS]

# ---------- PROMPT ----------
def build_prompt(items):
    lines = []
    for it in items:
        lines.append(f"[{it['lang'].upper()}][{it['topic']}] {it['title']} — {it['link']}")
    news_block = "\n".join(lines)

    prompt = f"""
You are the editor of "HelloWorld Intel PRO".

TASK:
Create a DAILY DIGEST draft based on the news items below.

RULES:
- Bilingual output: UA first (≈60%), then EN short (≈40%)
- Neutral, dry, professional tone
- NO financial advice, NO buy/sell signals
- Focus on enterprise impact, regulation, security, adoption, risks
- Max output length: {MAX_OUTPUT_TOKENS} tokens

STRUCTURE:

🧠 HelloWorld Intel PRO — Daily Digest (DRAFT)

UA:
1) AI / Tech — 3 bullets (what happened + why it matters)
2) Crypto / Regulation — 3 bullets (what + risks)
3) SAP / Enterprise — 2 bullets (impact for IT/CFO/security)

Risk flags (UA): 3 bullets
Signals to watch (UA): 4 bullets

EN (short):
4–6 bullets summarizing key enterprise signals.

NEWS ITEMS:
{news_block}
"""
    return prompt.strip()

# ---------- MAIN ----------
def build_daily_digest() -> str:
    if not OPENAI_API_KEY:
        return "⚠️ OpenAI API key not configured. Check .env (OPENAI_API_KEY)."

    items = fetch_top_items()
    prompt = build_prompt(items)

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a professional tech intelligence editor."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=MAX_OUTPUT_TOKENS,
            temperature=0.3
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"⚠️ OpenAI error: {e}"
