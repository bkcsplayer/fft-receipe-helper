"""Script to clear the current month's tab in Google Sheets."""

import os
import sys
import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Add backend directory to sys.path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.config import get_settings
from app.services.sheets_service import HEADERS

def get_sheets_service(settings):
    creds = Credentials.from_authorized_user_file(
        settings.GOOGLE_OAUTH_TOKEN_JSON, scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    return build("sheets", "v4", credentials=creds)

def reset_current_month_sheet():
    settings = get_settings()
    service = get_sheets_service(settings)
    spreadsheet_id = settings.GOOGLE_SHEETS_SPREADSHEET_ID
    
    now = datetime.datetime.now()
    tab_name = f"{now.year}/{now.month:02d}"
    
    print(f"Attempting to clear data in tab: '{tab_name}'")
    
    try:
        # Clear everything below the header
        range_to_clear = f"'{tab_name}'!A2:H"
        result = service.spreadsheets().values().clear(
            spreadsheetId=spreadsheet_id,
            range=range_to_clear,
        ).execute()
        
        print("Successfully cleared all data rows!")
        print(f"Cleared range: {result.get('clearedRange')}")
    except Exception as e:
        print(f"Failed to clear sheet: {e}")
        print("Note: If the tab does not exist yet, this error is expected.")

if __name__ == "__main__":
    confirm = input("Are you sure you want to clear all data for the current month? Type 'yes' to confirm: ")
    if confirm.lower() == 'yes':
        reset_current_month_sheet()
    else:
        print("Aborted.")
