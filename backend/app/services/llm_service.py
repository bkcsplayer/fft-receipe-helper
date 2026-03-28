"""LLM Service — calls MiniMax API for receipt OCR."""

import base64
import json
import logging
import httpx
import re

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
    """Send standardized receipt image to MiniMax and return structured data."""
    settings = get_settings()

    # image_bytes is already standardized as high-quality JPEG by main.py
    b64_image = base64.b64encode(image_bytes).decode("utf-8")
    media_type = content_type

    payload = {
        "model": settings.MINIMAX_MODEL,
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
        "Authorization": f"Bearer {settings.MINIMAX_API_KEY}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "https://api.minimax.io/v1/chat/completions",
            json=payload,
            headers=headers,
        )
        response.raise_for_status()

    data = response.json()
    raw_content = data["choices"][0]["message"]["content"].strip()
    logger.info("LLM raw response: %s", raw_content)

    # 1. Strip <think>...</think> blocks (Minimax M2.5)
    raw_content = re.sub(r'<think>.*?</think>', '', raw_content, flags=re.DOTALL).strip()

    # 2. Clean markdown fences if LLM wraps output
    if "```json" in raw_content:
        # Extract content between ```json and ```
        match = re.search(r'```json\s*(.*?)\s*```', raw_content, re.DOTALL)
        if match:
            raw_content = match.group(1).strip()
    elif "```" in raw_content:
        match = re.search(r'```\s*(.*?)\s*```', raw_content, re.DOTALL)
        if match:
            raw_content = match.group(1).strip()

    try:
        parsed = json.loads(raw_content)
    except json.JSONDecodeError as e:
        logger.error("Failed to parse JSON string string: %s", raw_content)
        raise e
        
    return ReceiptData(**parsed)
