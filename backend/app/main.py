"""FastAPI application — Receipt Helper backend."""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.models import ProcessResponse
from app.services.llm_service import extract_receipt_data
from app.services.drive_service import upload_receipt_image
from app.services.sheets_service import append_receipt_rows, get_month_data
from app.auth import verify_credentials
from datetime import datetime
from typing import List, Dict

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


@app.get("/api/history", response_model=List[Dict])
async def get_history(
    month: str = None,
    all_users: bool = False,
    username: str = Depends(verify_credentials)
):
    """
    Fetch all receipt rows for a given month (YYYY/MM) from Google Sheets.
    If no month provided, defaults to current month.
    """
    try:
        if not month:
            # Default to current YYYY/MM
            month = datetime.now().strftime("%Y/%m")
            
        logger.info("Fetching history for month %s by user %s (all_users=%s)", month, username, all_users)
        data = get_month_data(month)
        
        if all_users:
            return data
            
        # Filter by username so users only see their own data
        filtered_data = [row for row in data if row.get("上传者") == username]
        return filtered_data
        
    except Exception as e:
        logger.exception("Failed to fetch history")
        raise HTTPException(status_code=500, detail=f"Failed to fetch history: {str(e)}")


@app.post("/api/process-receipt", response_model=ProcessResponse)
async def process_receipt(
    file: UploadFile = File(...),
    username: str = Depends(verify_credentials)
):
    """
    Accept a receipt image, run it through the LLM for OCR,
    upload the original to Google Drive, and write item rows to Google Sheets.
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are accepted.")

    image_bytes = await file.read()
    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Acquire lock — only one receipt processed at a time
    async with processing_lock:
        try:
            # Step 1: LLM OCR
            logger.info("Processing receipt (%s, %d bytes) …", file.filename, len(image_bytes))
            receipt_data = await extract_receipt_data(image_bytes, file.content_type)
            logger.info("Extracted: %s — %d items", receipt_data.store_name, len(receipt_data.items))

            # Step 2: Upload to Google Drive
            drive_link = upload_receipt_image(image_bytes, receipt_data.date)

            # Step 3: Write rows to Google Sheets (including the uploader's username)
            rows_written = append_receipt_rows(receipt_data, drive_link, username)
            logger.info("Wrote %d rows to Sheets for user %s", rows_written, username)

            return ProcessResponse(
                success=True,
                receipt_data=receipt_data,
                drive_link=drive_link,
                message=f"成功处理 {len(receipt_data.items)} 件商品，已写入 Google Sheets。",
            )

        except Exception as e:
            logger.exception("Receipt processing failed")
            return ProcessResponse(
                success=False,
                message=f"处理失败: {str(e)}",
            )
