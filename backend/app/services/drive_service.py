"""Google Drive Service — upload receipt images with dynamic YYYY/MM folder routing."""

import logging
from io import BytesIO

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

from app.config import get_settings

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/drive"]


def _get_drive_service():
    """Authenticate and return a Drive API service instance."""
    settings = get_settings()
    creds = Credentials.from_authorized_user_file(
        settings.GOOGLE_OAUTH_TOKEN_JSON, scopes=SCOPES
    )
    return build("drive", "v3", credentials=creds)


def _find_folder(service, name: str, parent_id: str) -> str | None:
    """Find a folder by name under a given parent. Returns folder ID or None."""
    query = (
        f"name='{name}' and mimeType='application/vnd.google-apps.folder' "
        f"and '{parent_id}' in parents and trashed=false"
    )
    results = service.files().list(
        q=query, 
        fields="files(id, name)", 
        pageSize=1
    ).execute()
    files = results.get("files", [])
    return files[0]["id"] if files else None


def _create_folder(service, name: str, parent_id: str) -> str:
    """Create a folder under a given parent. Returns new folder ID."""
    metadata = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id],
    }
    folder = service.files().create(
        body=metadata, 
        fields="id"
    ).execute()
    logger.info("Created Drive folder '%s' (id=%s)", name, folder["id"])
    return folder["id"]


def _ensure_folder(service, name: str, parent_id: str) -> str:
    """Find or create a folder. Returns folder ID."""
    folder_id = _find_folder(service, name, parent_id)
    if folder_id:
        return folder_id
    return _create_folder(service, name, parent_id)


def _resolve_filename(service, folder_id: str, base_name: str) -> str:
    """Resolve collision: YYYY-MM-DD.jpg → YYYY-MM-DD_1.jpg → YYYY-MM-DD_2.jpg ..."""
    name = base_name
    suffix = 0
    while True:
        query = f"name='{name}' and '{folder_id}' in parents and trashed=false"
        results = service.files().list(
            q=query, 
            fields="files(id)", 
            pageSize=1
        ).execute()
        if not results.get("files"):
            return name
        suffix += 1
        stem = base_name.rsplit(".", 1)[0]
        ext = base_name.rsplit(".", 1)[1]
        name = f"{stem}_{suffix}.{ext}"


def upload_receipt_image(image_bytes: bytes, date_str: str) -> str:
    """
    Upload receipt image to Google Drive.

    Args:
        image_bytes: raw JPEG / PNG bytes
        date_str: receipt date in YYYY-MM-DD format

    Returns:
        Web view link to the uploaded file.
    """
    settings = get_settings()
    service = _get_drive_service()

    # Parse date parts
    parts = date_str.split("-")
    year, month = parts[0], parts[1]

    # Ensure YYYY/MM folder tree
    year_folder = _ensure_folder(service, year, settings.GOOGLE_DRIVE_ROOT_FOLDER_ID)
    month_folder = _ensure_folder(service, month, year_folder)

    # Determine unique filename
    base_name = f"{date_str}.jpg"
    final_name = _resolve_filename(service, month_folder, base_name)

    # Upload
    media = MediaIoBaseUpload(BytesIO(image_bytes), mimetype="image/jpeg", resumable=True)
    file_metadata = {"name": final_name, "parents": [month_folder]}
    uploaded = (
        service.files()
        .create(
            body=file_metadata, 
            media_body=media, 
            fields="id, webViewLink"
        )
        .execute()
    )

    # Make file readable by anyone with the link
    service.permissions().create(
        fileId=uploaded["id"],
        body={"type": "anyone", "role": "reader"}
    ).execute()

    link = uploaded.get("webViewLink", "")
    logger.info("Uploaded '%s' → %s", final_name, link)
    return link
