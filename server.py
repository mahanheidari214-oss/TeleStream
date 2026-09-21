import os
import re
import urllib.parse
import logging
from aiohttp import web

import database
from streamer import stream_file_chunks
from network_utils import format_size, get_lan_ip, make_safe_filename
from config import config

logger = logging.getLogger("server")

RANGE_REGEX = re.compile(r"^bytes=(\d*)-(\d*)$")

TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
PLAYER_TEMPLATE_PATH = os.path.join(TEMPLATE_DIR, "player.html")

# Define AppKeys to support modern aiohttp without warnings
try:
    TG_CLIENT_KEY = web.AppKey("tg_client")
    BOT_ME_KEY = web.AppKey("bot_me")
    PORT_KEY = web.AppKey("port")
except AttributeError:
    TG_CLIENT_KEY = "tg_client"
    BOT_ME_KEY = "bot_me"
    PORT_KEY = "port"

def get_base_url(request: web.Request) -> str:
    """Determine the public base URL based on config, Railway headers, or LAN IP."""
    custom_domain = config.get("custom_domain", "").strip()
    if custom_domain:
        return custom_domain.rstrip('/')

    # Check forward headers from reverse proxies (Railway / Render / Cloudflare)
    proto = request.headers.get("X-Forwarded-Proto", "http")
    host = request.headers.get("X-Forwarded-Host") or request.headers.get("Host")
    if host:
        return f"{proto}://{host}"

    lan_ip = get_lan_ip()
    port = request.app.get("port", 8080)
    return f"http://{lan_ip}:{port}"

async def handle_status(request: web.Request) -> web.Response:
    """JSON health check endpoint."""
    bot_me = request.app.get(BOT_ME_KEY)
    bot_name = getattr(bot_me, "username", "UnknownBot")
    return web.json_response({
        "status": "online",
        "bot": f"@{bot_name}",
        "engine": "TeleStream Kavimo Edition",
        "port": request.app.get(PORT_KEY, 8080)
    })

async def handle_index(request: web.Request) -> web.Response:
    """Server homepage with instructions and live status."""
    bot_me = request.app.get(BOT_ME_KEY)
    bot_name = getattr(bot_me, "username", "TeleStreamBot")
    bot_display = getattr(bot_me, "first_name", "TeleStream Instant")
    base_url = get_base_url(request)

    html = f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{bot_display} — پخش‌کننده و استریمر تلگرام</title>
    <link href="https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg: #07090e;
            --card: #0f121a;
            --border: rgba(255, 255, 255, 0.08);
            --primary: #06b6d4;
            --text: #f1f5f9;
            --muted: #94a3b8;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: 'Vazirmatn', sans-serif;
            background-color: var(--bg);
            color: var(--text);
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 20px;
        }}
        .card {{
            max-width: 580px;
            width: 100%;
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 32px;
            box-shadow: 0 12px 40px rgba(0,0,0,0.6);
            backdrop-filter: blur(20px);
        }}
        .badge {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(6, 182, 212, 0.15);
            color: var(--primary);
            border: 1px solid rgba(6, 182, 212, 0.4);
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 700;
            margin-bottom: 16px;
        }}
        .dot {{
            width: 8px;
            height: 8px;
            background: var(--primary);
            border-radius: 50%;
            box-shadow: 0 0 10px var(--primary);
        }}
        h1 {{ font-size: 24px; margin-bottom: 8px; font-weight: 800; }}
        p.sub {{ color: var(--muted); font-size: 14px; margin-bottom: 24px; }}
        .item {{
            display: flex;
            justify-content: space-between;
            padding: 12px 14px;
            background: rgba(255,255,255,0.03);
            border: 1px solid var(--border);
            border-radius: 12px;
            margin-bottom: 10px;
            font-size: 14px;
        }}
        .btn {{
            display: block;
            text-align: center;
            background: var(--primary);
            color: #000;
            text-decoration: none;
            padding: 14px;
            border-radius: 12px;
            font-weight: 700;
            margin-top: 24px;
            transition: transform 0.2s, opacity 0.2s;
        }}
        .btn:hover {{ opacity: 0.9; transform: scale(1.02); }}
    </style>
</head>
<body>
    <div class="card">
        <div class="badge"><span class="dot"></span> سرور آنلاین و فعال است</div>
        <h1>{bot_display}</h1>
        <p class="sub">پخش آنلاین ابری تلگرام با پلیر اختصاصی کاویمو و استریم مستقیم برای ADM</p>

        <div class="item">
            <span>ربات تلگرام:</span>
            <span style="color: var(--primary); font-weight: 700; direction: ltr;">@{bot_name}</span>
        </div>
        <div class="item">
            <span>آدرس عمومی سرور:</span>
            <span style="direction: ltr;">{base_url}</span>
        </div>
        <div class="item">
            <span>پشتیبانی از HTTP 206 (Range):</span>
            <span style="color: #10b981; font-weight: 700;">فعال (پخش روان بدون بارگیری کل فایل)</span>
        </div>
        <div class="item">
            <span>موتور پخش‌کننده:</span>
            <span style="color: #f59e0b; font-weight: 700;">طراحی اختصاصی کاویمو • بیوماز</span>
        </div>

        <a class="btn" href="https://t.me/{bot_name}" target="_blank">ارسال ویدیو در ربات تلگرام ↗</a>
    </div>
</body>
</html>
"""
    return web.Response(text=html, content_type="text/html", charset="utf-8")

async def handle_player(request: web.Request) -> web.Response:
    """Serves the Kavimo / Biomaz HTML5 web player."""
    link_id = request.match_info.get("link_id")
    if not link_id:
        return web.Response(status=404, text="لینک نامعتبر است")

    record = await database.get_media(link_id)
    if not record:
        return web.Response(status=404, text="فایل یافت نشد یا منقضی شده است")

    file_name = record["file_name"] or f"video_{link_id}.mp4"
    file_size = format_size(record["file_size"])
    safe_name = make_safe_filename(file_name)
    encoded_name = urllib.parse.quote(safe_name)

    base_url = get_base_url(request)
    stream_url = f"{base_url}/stream/{link_id}/{encoded_name}"
    dl_url = f"{base_url}/dl/{link_id}/{encoded_name}"
    # VLC / MX Player intent link
    vlc_url = f"vlc://{stream_url}"

    try:
        with open(PLAYER_TEMPLATE_PATH, "r", encoding="utf-8") as f:
            template = f.read()

        html = (template
            .replace("{{ file_name }}", file_name)
            .replace("{{ file_size }}", file_size)
            .replace("{{ stream_url }}", stream_url)
            .replace("{{ dl_url }}", dl_url)
            .replace("{{ vlc_url }}", vlc_url)
        )
        return web.Response(text=html, content_type="text/html", charset="utf-8")
    except Exception as e:
        logger.error(f"Error rendering player template: {e}")
        return web.Response(status=500, text=f"خطا در بارگذاری پلیر: {e}")

async def handle_stream(request: web.Request) -> web.StreamResponse:
    """Handles HTTP 206 Partial Content Range streaming for video players (inline)."""
    return await _serve_media(request, is_attachment=False)

async def handle_download(request: web.Request) -> web.StreamResponse:
    """Handles HTTP 206 Partial Content Range streaming for download managers (attachment)."""
    return await _serve_media(request, is_attachment=True)

async def _serve_media(request: web.Request, is_attachment: bool = False) -> web.StreamResponse:
    link_id = request.match_info.get("link_id")
    if not link_id:
        return web.Response(status=404, text="Invalid link ID")

    record = await database.get_media(link_id)
    if not record:
        return web.Response(status=404, text="File link expired or not found")

    client = request.app[TG_CLIENT_KEY]
    chat_id = record["chat_id"]
    message_id = record["message_id"]
    file_id = record["file_id"]
    file_size = record["file_size"]
    file_name = record["file_name"] or f"file_{link_id}.bin"
    mime_type = record["mime_type"] or "video/mp4"

    # Ensure browser video player receives a video content-type
    if not is_attachment and ("video" not in mime_type.lower() and "audio" not in mime_type.lower()):
        if file_name.lower().endswith((".mp4", ".m4v")):
            mime_type = "video/mp4"
        elif file_name.lower().endswith(".mkv"):
            mime_type = "video/x-matroska"
        elif file_name.lower().endswith(".webm"):
            mime_type = "video/webm"
        elif file_name.lower().endswith(".mp3"):
            mime_type = "audio/mpeg"

    safe_name = make_safe_filename(file_name)
    encoded_name = urllib.parse.quote(safe_name)

    disposition_type = "attachment" if is_attachment else "inline"
    headers = {
        "Accept-Ranges": "bytes",
        "Content-Type": mime_type,
        "Content-Disposition": f'{disposition_type}; filename="{safe_name}"; filename*=UTF-8\'\'{encoded_name}',
        "Cache-Control": "public, max-age=86400",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Range, Content-Type",
    }

    range_header = request.headers.get("Range")
    if range_header:
        match = RANGE_REGEX.match(range_header.strip())
        if not match:
            return web.Response(
                status=416,
                headers={"Content-Range": f"bytes */{file_size}"},
                text="Requested Range Not Satisfiable"
            )

        start_str, end_str = match.groups()
        start = int(start_str) if start_str else 0
        end = int(end_str) if end_str else (file_size - 1)

        if start >= file_size or end >= file_size or start > end:
            return web.Response(
                status=416,
                headers={"Content-Range": f"bytes */{file_size}"},
                text="Requested Range Not Satisfiable"
            )

        content_length = end - start + 1
        headers["Content-Range"] = f"bytes {start}-{end}/{file_size}"
        headers["Content-Length"] = str(content_length)

        response = web.StreamResponse(status=206, headers=headers)
        await response.prepare(request)

        try:
            async for chunk in stream_file_chunks(client, chat_id, message_id, file_id, file_size, start, end):
                await response.write(chunk)
            await response.write_eof()
        except (ConnectionResetError, BrokenPipeError):
            logger.debug(f"Client disconnected early from range {start}-{end}")
        except Exception as e:
            logger.error(f"Error during streaming range: {e}")
        return response

    # Full file request
    headers["Content-Length"] = str(file_size)
    response = web.StreamResponse(status=200, headers=headers)
    await response.prepare(request)

    try:
        async for chunk in stream_file_chunks(client, chat_id, message_id, file_id, file_size, 0, file_size - 1):
            await response.write(chunk)
        await response.write_eof()
    except (ConnectionResetError, BrokenPipeError):
        logger.debug(f"Client disconnected early from full file stream")
    except Exception as e:
        logger.error(f"Error during full stream: {e}")

    return response

def create_app(tg_client, bot_me, port: int) -> web.Application:
    """Initialize the aiohttp application with all routes."""
    app = web.Application()
    app[TG_CLIENT_KEY] = tg_client
    app[BOT_ME_KEY] = bot_me
    app[PORT_KEY] = port

    app.router.add_get("/", handle_index)
    app.router.add_get("/status", handle_status)
    app.router.add_get("/play/{link_id}", handle_player)
    app.router.add_get("/stream/{link_id}", handle_stream)
    app.router.add_get("/stream/{link_id}/{filename}", handle_stream)
    app.router.add_get("/dl/{link_id}", handle_download)
    app.router.add_get("/dl/{link_id}/{filename}", handle_download)

    return app
