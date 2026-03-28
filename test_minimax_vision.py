import asyncio
import base64
import httpx

MINIMAX_API_KEY = "sk-api-b85KvoPAm3WTkwKiPIYTnL52ohyf0yoTHD-7u0Uh9V5KqTvD3Y8652bfLsYWwHFNHR12Z4E_mABoquUM4APumQQFnIKxxclvXEyGXu3qnQGH3BrgmtXshJs"
MINIMAX_MODEL = "MiniMax-M2.5"

async def test():
    # A tiny 1x1 transparent png, base64 encoded
    tiny_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="

    payload = {
        "model": MINIMAX_MODEL,
        "messages": [
            {"role": "system", "content": "Return only a valid JSON: {\"test\": 1}"},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{tiny_image_b64}"
                        },
                    },
                    {
                        "type": "text",
                        "text": "Please extract information from this image.",
                    },
                ],
            },
        ],
        "max_tokens": 1000,
        "temperature": 0.1,
    }

    headers = {
        "Authorization": f"Bearer {MINIMAX_API_KEY}",
        "Content-Type": "application/json",
    }

    print("Sending request to MiniMax...")
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "https://api.minimax.io/v1/chat/completions",
            json=payload,
            headers=headers,
        )
        print("Status code:", response.status_code)
        print("Response body:", response.text)

if __name__ == "__main__":
    asyncio.run(test())
