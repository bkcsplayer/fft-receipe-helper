"""LLM Service — calls OpenRouter API with Claude 3.5 Sonnet for receipt OCR."""

import base64
import json
import logging
import httpx

from app.config import get_settings
from app.models import ReceiptData

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a master-level receipt OCR expert and data analyst.
Analyze the receipt image carefully. Before extracting the data, you MUST provide a step-by-step thinking process in the "reasoning" field.

You MUST return ONLY valid JSON in this exact format — no extra text, no markdown fences:
{
  "reasoning": "Step 1: Check image orientation (rotate mentally if sideways). Step 2: Identify store name and date. Step 3: Scan all items. If an item has sub-items (like 'Queen Chicken' under '2 Items with Rice') or modifiers, merge them into the parent item's product_name instead of creating new items. Step 4: Find the GRAND TOTAL (including tips and taxes, usually at the bottom).",
  "date": "YYYY-MM-DD",
  "store_name": "店名",
  "items": [
    {"product_name": "商品名称 (include all sub-items/modifiers here)", "price": 0.00}
  ],
  "total_price": 0.00,
  "tax": 0.00
}

CRITICAL RULES:
1. ALWAYS start with the "reasoning" field to explain your extraction logic and avoid hallucinations.
2. If the image is rotated, mentally rotate it before reading. Do NOT guess a random store like CVS.
3. Sub-items (e.g. choice of meat, sides) or items without a price MUST be appended to the parent `product_name`. Do NOT list them as separate items. For example "1 雙拼飯" with "Queen Chicken" and "Roasted Duck" should be ONE item named "1 雙拼飯 (Queen Chicken, Roasted Duck)" and its price.
4. `total_price` MUST be the final actual amount charged to the credit card (Grand Total including any Tips and Taxes).
5. All prices must be numbers (float), not strings.
6. date must be in YYYY-MM-DD format. Infer the year if missing but context is clear.
"""


async def extract_receipt_data(image_bytes: bytes, content_type: str = "image/jpeg") -> ReceiptData:
    """Send standardized receipt image to OpenRouter and return structured data."""
    settings = get_settings()

    # image_bytes is already standardized as high-quality JPEG by main.py
    b64_image = base64.b64encode(image_bytes).decode("utf-8")
    media_type = content_type

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
        "response_format": {"type": "json_object"}
    }

    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://receipt-helper.app",
        "X-Title": "Receipt Helper",
    }

    async with httpx.AsyncClient(timeout=90.0) as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            json=payload,
            headers=headers,
        )
        response.raise_for_status()

    data = response.json()
    raw_content = data["choices"][0]["message"]["content"].strip()
    logger.info("LLM raw response via OpenRouter: %s", raw_content)

    # Clean markdown fences if LLM wraps output
    import re
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_content, re.DOTALL)
    if match:
        raw_content = match.group(1)
    else:
        # try to find first { and last }
        start = raw_content.find('{')
        end = raw_content.rfind('}')
        if start != -1 and end != -1:
            raw_content = raw_content[start:end+1]

    parsed = json.loads(raw_content)
    return ReceiptData(**parsed)
