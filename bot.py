import os
import sys
import secrets
import logging
import asyncio
import urllib.parse
from datetime import datetime

# Configure UTF-8 encoding for Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Load C-crypto patch and Network routing patch
import crypto_patch
from net_patch import apply_net_patch
apply_net_patch()

from hydrogram import Client, filters
from hydrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web

from config import config
import database
from network_utils import get_lan_ip, format_size, format_duration, make_safe_filename
from server import create_app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s: %(message)s"
)
logger = logging.getLogger("bot")

def get_media_info(message: Message):
    for kind in ("video", "document", "animation", "audio", "voice"):
        media = getattr(message, kind, None)
        if media is not None:
            file_name = getattr(media, "file_name", None) or f"{kind}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
            mime_type = getattr(media, "mime_type", "video/mp4")
            file_size = getattr(media, "file_size", 0)
            file_id = getattr(media, "file_id", "")
            duration = getattr(media, "duration", 0)
            return kind, file_id, file_name, file_size, mime_type, duration
    return None, None, None, None, None, 0

def is_authorized(user_id: int) -> bool:
    allowed = config.get("allowed_users") or []
    if not allowed:
        return True
    return user_id in allowed

async def main():
    # 1. Initialize SQLite Database
    await database.init_db()

    port = int(config.get("port", 8080))
    bind_ip = config.get("bind_address", "0.0.0.0")

    # Validate Telegram credentials
    api_id = config.get("api_id")
    api_hash = config.get("api_hash")
    bot_token = config.get("bot_token")

    if not api_id or not api_hash or not bot_token:
        print("\n" + "!" * 60)
        print("  [ERROR] Missing required Telegram credentials!")
        print("  Please provide API_ID, API_HASH, and BOT_TOKEN via:")
        print("  1. Railway Environment Variables, OR")
        print("  2. config.json in the project root directory.")
        print("!" * 60 + "\n")
        sys.exit(1)

    # 2. Initialize Hydrogram Bot Client
    app = Client(
        "telestream_kavimo_bot",
        api_id=api_id,
        api_hash=api_hash,
        bot_token=bot_token,
        in_memory=True
    )

    @app.on_message(filters.command(["start", "help"]))
    async def start_handler(client: Client, message: Message):
        user_id = message.from_user.id if message.from_user else 0
        if not is_authorized(user_id):
            await message.reply_text(
                f"⛔ **دسترسی غیرمجاز است**\n\nشناسه کاربری شما: `{user_id}`\n"
                "برای فعال‌سازی، این شناسه را به متغیر `ALLOWED_USERS` اضافه کنید."
            )
            return

        lan_ip = get_lan_ip()
        custom_domain = config.get("custom_domain", "").strip()
        display_host = custom_domain if custom_domain else f"http://{lan_ip}:{port}"

        welcome_text = (
            "🎬 **به TeleStream Instant (نسخه کاویمو) خوش آمدید!**\n\n"
            "⚡ **استریم مستقیم و آنلاین ویدیوهای تلگرام بدون اشغال حافظه گوشی**\n\n"
            f"🌐 **آدرس سرور:** `{display_host}`\n"
            "🟢 **وضعیت سرور:** آنلاین و آماده به کار\n\n"
            "📖 **راهنمای استفاده:**\n"
            "۱. هر فیلم، انیمه یا ویدیویی را از هر کانال یا پیامی به این ربات فوروارد (ارسال) کنید.\n"
            "۲. ربات فوراً لینک پخش اختصاصی در **پلیر کاویمو (مشابه بیوماز)** را برای شما می‌فرستد.\n"
            "۳. روی دکمه **«تماشای آنلاین»** کلیک کنید و در کمتر از ۲ ثانیه ویدیو را روان و با کیفیت اصلی تماشا کنید!\n\n"
            "💡 *امکان کنترل سرعت پخش (از 0.5x تا 2.5x)، پرش ۱۰ ثانیه‌ای و دابل‌تپ موبایل فعال است.*"
        )
        await message.reply_text(welcome_text)

    @app.on_message(filters.command("myid"))
    async def myid_handler(client: Client, message: Message):
        user_id = message.from_user.id if message.from_user else 0
        await message.reply_text(f"👤 شناسه کاربری شما: `{user_id}`")

    @app.on_message(filters.incoming & (filters.document | filters.video | filters.audio | filters.voice | filters.animation))
    async def media_handler(client: Client, message: Message):
        user_id = message.from_user.id if message.from_user else 0
        if not is_authorized(user_id):
            await message.reply_text(f"⛔ دسترسی غیرمجاز. شناسه: `{user_id}`")
            return

        kind, file_id, file_name, file_size, mime_type, duration = get_media_info(message)
        if not file_id:
            await message.reply_text("❌ فایلی برای پخش شناسایی نشد.")
            return

        # Unique 10-hex short link ID
        link_id = secrets.token_hex(5)

        # Save to async SQLite database
        await database.save_media(
            link_id=link_id,
            chat_id=message.chat.id,
            message_id=message.id,
            file_id=file_id,
            file_name=file_name,
            file_size=file_size,
            mime_type=mime_type,
            duration=duration
        )

        lan_ip = get_lan_ip()
        custom_domain = config.get("custom_domain", "").strip()
        base_url = custom_domain.rstrip('/') if custom_domain else f"http://{lan_ip}:{port}"

        safe_name = make_safe_filename(file_name)
        encoded_name = urllib.parse.quote(safe_name)

        play_url = f"{base_url}/play/{link_id}"
        stream_url = f"{base_url}/stream/{link_id}/{encoded_name}"
        dl_url = f"{base_url}/dl/{link_id}/{encoded_name}"

        readable_size = format_size(file_size)
        duration_str = format_duration(duration) if duration > 0 else "—"

        caption = (
            f"🎬 **{file_name}**\n"
            f"📦 **حجم:** `{readable_size}` | ⏱ **مدت زمان:** `{duration_str}`\n"
            f"⚡ **وضعیت:** آماده پخش بدون دانلود کل فایل\n\n"
            f"🌐 **پلیر اختصاصی کاویمو (بیوماز):**\n"
            f"{play_url}\n\n"
            f"📱 **لینک استریم (VLC / MX Player):**\n"
            f"`{stream_url}`\n\n"
            f"📥 **لینک دانلود مستقیم (ADM / IDM):**\n"
            f"`{dl_url}`"
        )

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎬 تماشای آنلاین (پلیر کاویمو)", url=play_url)],
            [
                InlineKeyboardButton("📱 استریم در VLC / MX", url=stream_url),
                InlineKeyboardButton("⚡ دانلود با ADM", url=dl_url)
            ]
        ])

        await message.reply_text(caption, reply_markup=keyboard)

    print("\n" + "=" * 60)
    print("  🚀 TeleStream Instant (Kavimo Edition) Is Starting...")
    print("=" * 60)

    # 3. Start Telegram Client
    await app.start()
    bot_me = await app.get_me()
    print(f"  [+] Telegram Bot Connected: @{bot_me.username} ({bot_me.first_name})")

    # 4. Start aiohttp Web Server
    web_app = create_app(app, bot_me, port)
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, bind_ip, port)
    await site.start()

    lan_ip = get_lan_ip()
    custom_domain = config.get("custom_domain", "").strip()
    active_host = custom_domain if custom_domain else f"http://{lan_ip}:{port}"
    print(f"  [+] Web Player & Streamer Ready at: {active_host}")
    print(f"  [+] Port: {port} | Bind: {bind_ip}")
    print("=" * 60 + "\n")

    # 5. Keep both running
    try:
        while True:
            await asyncio.sleep(3600)
    finally:
        await runner.cleanup()
        await app.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\n[!] TeleStream Engine Stopped cleanly.")
