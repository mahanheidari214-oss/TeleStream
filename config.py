import json
import os
import sys

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

DEFAULT_CONFIG = {
    "api_id": 0,
    "api_hash": "",
    "bot_token": "",
    "allowed_users": [],
    "port": 8080,
    "bind_address": "0.0.0.0",
    "custom_domain": "",
    "player_title": "TeleStream Player",
    "theme_brand": "Kavimo"
}

def load_config() -> dict:
    config = dict(DEFAULT_CONFIG)

    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8-sig") as f:
                config.update(json.load(f))
        except Exception as e:
            print(f"[!] Warning reading config.json: {e}")

    # Environment variables override config.json (essential for cloud platforms like Railway)
    api_id_env = os.environ.get("TELEGRAM_API_ID") or os.environ.get("API_ID")
    if api_id_env:
        try:
            config["api_id"] = int(api_id_env)
        except ValueError:
            pass

    api_hash_env = os.environ.get("TELEGRAM_API_HASH") or os.environ.get("API_HASH")
    if api_hash_env:
        config["api_hash"] = api_hash_env.strip()

    bot_token_env = os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("BOT_TOKEN")
    if bot_token_env:
        config["bot_token"] = bot_token_env.strip()

    port_env = os.environ.get("PORT")
    if port_env:
        try:
            config["port"] = int(port_env)
        except ValueError:
            pass

    # Auto-detect Cloud Public Domains (Railway, Render, or Custom)
    railway_domain = os.environ.get("RAILWAY_PUBLIC_DOMAIN")
    if railway_domain:
        domain = railway_domain.strip()
        if not domain.startswith("http"):
            domain = "https://" + domain
        config["custom_domain"] = domain
    elif os.environ.get("RENDER_EXTERNAL_URL"):
        config["custom_domain"] = os.environ["RENDER_EXTERNAL_URL"].strip()
    elif os.environ.get("CUSTOM_DOMAIN"):
        config["custom_domain"] = os.environ["CUSTOM_DOMAIN"].strip()

    allowed_env = os.environ.get("TELEGRAM_CHAT_IDS") or os.environ.get("ALLOWED_USERS")
    if allowed_env:
        try:
            ids = [int(x.strip()) for x in allowed_env.split(",") if x.strip()]
            config["allowed_users"] = ids
        except Exception:
            pass

    return config

config = load_config()
