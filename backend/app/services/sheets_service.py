"""Google Sheets Service — append receipt data as line-item rows."""

import logging
from typing import List, Dict

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app.config import get_settings
from app.models import ReceiptData

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Column headers for each tab
HEADERS = ["日期", "上传者", "店名", "商品名称", "单价", "总价(小票级)", "税费(小票级)", "小票图片链接(Drive)"]


def _get_sheets_service():
    """Authenticate and return a Sheets API service instance."""
    settings = get_settings()
    creds = Credentials.from_authorized_user_file(
        settings.GOOGLE_OAUTH_TOKEN_JSON, scopes=SCOPES
    )
    return build("sheets", "v4", credentials=creds)


def _ensure_tab(service, spreadsheet_id: str, tab_name: str) -> None:
    """Find or create a tab (sheet) with the given name, adding headers if new."""
    meta = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    existing = [s["properties"]["title"] for s in meta.get("sheets", [])]

    if tab_name in existing:
        return

    # Create new tab
    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={
            "requests": [
                {"addSheet": {"properties": {"title": tab_name}}}
            ]
        },
    ).execute()
    logger.info("Created Sheets tab '%s'", tab_name)

    # Write header row
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=f"'{tab_name}'!A1",
        valueInputOption="RAW",
        body={"values": [HEADERS]},
    ).execute()


def append_receipt_rows(receipt: ReceiptData, drive_link: str, uploader: str) -> int:
    """
    Append N rows to the spreadsheet (one row per item).

    Returns:
        Number of rows appended.
    """
    settings = get_settings()
    service = _get_sheets_service()
    spreadsheet_id = settings.GOOGLE_SHEETS_SPREADSHEET_ID

    # Tab name: YYYY/MM
    parts = receipt.date.split("-")
    tab_name = f"{parts[0]}/{parts[1]}"

    _ensure_tab(service, spreadsheet_id, tab_name)

    # Build rows — one per item, with receipt-level totals repeated
    rows = []
    for item in receipt.items:
        rows.append([
            receipt.date,
            uploader,
            receipt.store_name,
            item.product_name,
            item.price,
            receipt.total_price,
            receipt.tax,
            drive_link,
        ])

    if not rows:
        logger.warning("No items to write for receipt dated %s", receipt.date)
        return 0

    service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range=f"'{tab_name}'!A:H",
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body={"values": rows},
    ).execute()

    logger.info("Appended %d rows to tab '%s'", len(rows), tab_name)
    return len(rows)

def get_month_data(month_str: str) -> List[Dict]:
    """
    Read all rows from a specific month tab (e.g., 'YYYY/MM').
    Returns a list of dictionaries mapping headers to row values.
    """
    settings = get_settings()
    service = _get_sheets_service()
    spreadsheet_id = settings.GOOGLE_SHEETS_SPREADSHEET_ID
    
    # Check if tab exists
    meta = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    existing = [s["properties"]["title"] for s in meta.get("sheets", [])]
    
    if month_str not in existing:
        return []

    # Get data
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=f"'{month_str}'!A:H"
    ).execute()
    
    values = result.get('values', [])
    if not values or len(values) < 2: # No data or only headers
        return []
        
    # The first row is headers (index 0)
    # HEADERS = ["日期", "上传者", "店名", "商品名称", "单价", "总价(小票级)", "税费(小票级)", "小票图片链接(Drive)"]
    headers = values[0]
    data = []
    
    for row in values[1:]:
        # Pad row with empty strings if it's shorter than headers
        padded_row = row + [""] * (len(headers) - len(row))
        item = {headers[i]: padded_row[i] for i in range(len(headers))}
        data.append(item)
        
    return data
