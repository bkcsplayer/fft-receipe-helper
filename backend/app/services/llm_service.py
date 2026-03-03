"""LLM Service — calls OpenRouter API with Claude 3.5 Sonnet for receipt OCR."""

import base64
import json
import logging
import httpx
import io
from PIL import Image

from app.config import get_settings
from app.models import ReceiptData

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a receipt OCR expert. Analyze the receipt image and extract structured data.

You MUST return ONLY valid JSON in this exact format — no extra text, no markdown fences:
{
  "date": "YYYY-MM-DD",
  "store_name": "店名",
  "items": [
    {"product_name": "商品名称", "price": 0.00}
  ],
  "total_price": 0.00,
  "tax": 0.00
}

Rules:
- date must be in YYYY-MM-DD format. If the year is missing, infer the most likely year.
- price is the unit price per item. If quantity > 1 and only total line price is shown, divide by quantity.
- total_price is the grand total shown on the receipt.
- tax is the tax amount. If no tax line exists, set to 0.
- All prices must be numbers (float), not strings.
- If a field cannot be determined, use reasonable defaults (empty string for text, 0.0 for numbers).
"""


async def extract_receipt_data(image_bytes: bytes, content_type: str = "image/jpeg") -> ReceiptData:
    """Send receipt image to OpenRouter (Claude 3.5 Sonnet) and return structured data."""
    settings = get_settings()

    # Process image with Pillow to compress and resize
    try:
        img = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB to handle RGBA/transparent PNGs and standardize format
        if img.mode != 'RGB':
            img = img.convert('RGB')
            
        # Resize if dimensions are too large (1600px max)
        max_size = 1600
        if img.width > max_size or img.height > max_size:
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
        # Save as compressed JPEG
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=85)
        processed_bytes = buffer.getvalue()
        logger.info("Image processed and compressed from %d to %d bytes", len(image_bytes), len(processed_bytes))
        
        # We enforce JPEG after processing
        media_type = "image/jpeg"
    except Exception as e:
        logger.warning("Pillow image processing failed: %s. Falling back to original bytes.", str(e))
        processed_bytes = image_bytes
        media_type = content_type if content_type in ("image/jpeg", "image/png", "image/webp", "image/gif") else "image/jpeg"

    # Encode image to base64
    b64_image = base64.b64encode(processed_bytes).decode("utf-8")

    payload = {
        "model": settings.OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{media_type};base64,{b64_image}"
                        },
                    },
                    {
                        "type": "text",
                        "text": "Please extract all information from this receipt image and return the JSON.",
                    },
                ],
            },
        ],
        "max_tokens": 2000,
        "temperature": 0.1,
    }

    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://receipt-helper.app",
        "X-Title": "Receipt Helper",
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            json=payload,
            headers=headers,
        )
        response.raise_for_status()

    data = response.json()
    raw_content = data["choices"][0]["message"]["content"].strip()
    logger.info("LLM raw response: %s", raw_content)

    # Clean markdown fences if LLM wraps output
    if raw_content.startswith("```"):
        lines = raw_content.split("\n")
        raw_content = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    parsed = json.loads(raw_content)
    return ReceiptData(**parsed)
