"""FastAPI application — Receipt Helper backend."""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.models import ProcessResponse, SaveReceiptRequest
from app.services.llm_service import extract_receipt_data
from app.services.drive_service import upload_receipt_image
from app.services.sheets_service import append_receipt_rows, get_month_data
from app.services.telegram_service import send_telegram_photo
from app.auth import verify_credentials
from datetime import datetime
import traceback
from typing import List, Dict
import io
from PIL import Image

def standardize_image_for_upload(image_bytes: bytes) -> bytes:
    """Read image bytes, convert to RGB, resize (max 2000px), and return high quality JPEG bytes."""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        max_size = 2000
        if img.width > max_size or img.height > max_size:
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=90)
        return buffer.getvalue()
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.warning("Image standardization failed: %s. Falling back to original.", str(e))
        return image_bytes
# ── Logging ──────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)

# ── Mutex lock (lightweight concurrency guard) ───────────────────────
processing_lock = asyncio.Lock()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown hooks."""
    logger.info("Receipt Helper backend starting …")
    yield
    logger.info("Receipt Helper backend shutting down …")


# ── App ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="Receipt Helper API",
    description="智能小票管家 — OCR + Google Drive + Google Sheets",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────────
settings = get_settings()
origins = [o.strip() for o in settings.BACKEND_CORS_ORIGINS.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routes ───────────────────────────────────────────────────────────
@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/auth/verify")
async def verify_auth(username: str = Depends(verify_credentials)):
    """
    Verify credentials provided via Basic Auth and return success.
    The actual validation is handled by the Depends(verify_credentials) dependency.
    """
    return {"success": True, "username": username}


@app.get("/api/history", response_model=List[Dict])
async def get_history(
    month: str = None,
    all_users: bool = False,
    username: str = Depends(verify_credentials)
):
    """
    Fetch all receipt rows for a given month (YYYY/MM) or 'all' from Google Sheets.
    If no month provided, defaults to 'all'.
    """
    try:
        if not month:
            month = "all"
            
        logger.info("Fetching history for month %s by user %s (all_users=%s)", month, username, all_users)
        data = get_month_data(month)
        
        if all_users:
            return data
            
        # Filter by username so users only see their own data
        # For 'admin' (or legacy data), if '上传者' is missing, assume it belongs to admin
        filtered_data = []
        for row in data:
            uploader = row.get("上传者")
            if uploader == username:
                filtered_data.append(row)
            elif not uploader and username == "admin":
                filtered_data.append(row)
                
        return filtered_data
        
    except Exception as e:
        logger.exception("Failed to fetch history")
        raise HTTPException(status_code=500, detail=f"Failed to fetch history: {str(e)}")


@app.post("/api/parse-receipt", response_model=ProcessResponse)
async def parse_receipt(
    file: UploadFile = File(...),
    username: str = Depends(verify_credentials)
):
    """
    Accept a receipt image, run it through the LLM for OCR,
    upload the original to Google Drive.
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are accepted.")

    image_bytes = await file.read()
    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Standardize image to JPEG with optimized size before sending to LLM and Drive
    standardized_bytes = standardize_image_for_upload(image_bytes)

    # Acquire lock — only one receipt processed at a time
    async with processing_lock:
        try:
            # Step 1: LLM OCR
            logger.info("Parsing receipt (%s, %d bytes -> %d bytes) ...", file.filename, len(image_bytes), len(standardized_bytes))
            # Pass optimized bytes to LLM, enforcing image/jpeg
            receipt_data = await extract_receipt_data(standardized_bytes, "image/jpeg")
            logger.info("Extracted: %s — %d items", receipt_data.store_name, len(receipt_data.items))

            # Step 2: Upload to Google Drive (using optimized JPEG directly)
            drive_link = upload_receipt_image(standardized_bytes, receipt_data.date)

            # Fire Telegram notification asynchronously without blocking response
            asyncio.create_task(send_telegram_photo(
                image_bytes=standardized_bytes,
                caption=f"✅ <b>小票解析成功</b>\n门店: {receipt_data.store_name}\n日期: {receipt_data.date}\n总计: <b>${receipt_data.total_price}</b>\n商品数: {len(receipt_data.items)} 件\n\n<a href='{drive_link}'>查看原图 (Google Drive)</a>"
            ))

            return ProcessResponse(
                success=True,
                receipt_data=receipt_data,
                drive_link=drive_link,
                message=f"成功解析 {len(receipt_data.items)} 件商品，请确认后保存。",
            )

        except Exception as e:
            logger.exception("Receipt parsing failed")
            # Fallback to standardized bytes or original bytes if standardizing failed
            target_bytes = standardized_bytes if 'standardized_bytes' in locals() else image_bytes
            asyncio.create_task(send_telegram_photo(
                image_bytes=target_bytes,
                caption=f"❌ <b>解析及提取崩溃报警</b>\n上传账号: {username}\n\n<b>错误详情:</b>\n<pre>{str(e)}</pre>"
            ))
            return ProcessResponse(
                success=False,
                message=f"解析失败: {str(e)}",
            )

@app.post("/api/save-receipt", response_model=ProcessResponse)
async def save_receipt(
    request: SaveReceiptRequest,
    username: str = Depends(verify_credentials)
):
    """
    Save the confirmed receipt data to Google Sheets.
    """
    try:
        # Step 3: Write rows to Google Sheets (including the uploader's username)
        rows_written = append_receipt_rows(request.receipt_data, request.drive_link or "", username)
        logger.info("Wrote %d rows to Sheets for user %s", rows_written, username)

        return ProcessResponse(
            success=True,
            receipt_data=request.receipt_data,
            drive_link=request.drive_link,
            message=f"成功保存 {len(request.receipt_data.items)} 件商品至 Google Sheets。",
        )
    except Exception as e:
        logger.exception("Receipt saving failed")
        return ProcessResponse(
            success=False,
            message=f"保存失败: {str(e)}",
        )
