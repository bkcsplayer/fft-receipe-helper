"""Telegram Service — sends notification messages/photos on success and failure."""

import httpx
import logging
from app.config import get_settings

logger = logging.getLogger(__name__)

async def send_telegram_message(text: str):
    """Send a plain text message to the configured Telegram chat."""
    settings = get_settings()
    if not settings.ENABLE_TELEGRAM_NOTIFICATIONS or not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        return
        
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": settings.TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
    except Exception as e:
        logger.warning("Failed to send text to Telegram: %s", str(e))

async def send_telegram_photo(image_bytes: bytes, caption: str):
    """Send an image along with a text caption to Telegram."""
    settings = get_settings()
    if not settings.ENABLE_TELEGRAM_NOTIFICATIONS or not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        return
        
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendPhoto"
    data = {
        "chat_id": settings.TELEGRAM_CHAT_ID,
        "caption": caption,
        "parse_mode": "HTML"
    }
    files = {
        "photo": ("receipt.jpg", image_bytes, "image/jpeg")
    }
    
    try:
        # We need a new timeout since uploads might take slightly longer
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(url, data=data, files=files)
            response.raise_for_status()
    except Exception as e:
        logger.warning("Failed to send photo to Telegram: %s", str(e))
        # Fallback: try sending just the text if photo upload fails
        await send_telegram_message(caption)
