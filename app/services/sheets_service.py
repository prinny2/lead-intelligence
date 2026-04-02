"""Optional Google Sheets write-back for scored leads.

Set GOOGLE_SHEETS_ID and GOOGLE_CREDENTIALS_JSON (service account JSON string)
env vars to enable. If either is missing the module silently skips.
"""

import json
import logging
import os
from datetime import UTC, datetime

logger = logging.getLogger("lead_intelligence")

_HEADERS = [
    "timestamp", "name", "city", "state",
    "score", "decision", "urgency", "whatsapp_message",
]


def _get_sheet():
    """Return a gspread worksheet, or None if not configured."""
    sheet_id = os.getenv("GOOGLE_SHEETS_ID", "").strip()
    creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON", "").strip()
    if not sheet_id or not creds_json:
        return None
    try:
        import gspread
        from google.oauth2.service_account import Credentials

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds_dict = json.loads(creds_json)
        credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        gc = gspread.authorize(credentials)
        return gc.open_by_key(sheet_id).sheet1
    except Exception as exc:
        logger.warning("sheets_unavailable reason=%s", exc)
        return None


def _ensure_header(sheet) -> None:
    """Write header row if the sheet is empty."""
    try:
        cell = sheet.cell(1, 1).value
        if not cell:
            sheet.insert_row(_HEADERS, 1)
    except Exception as exc:
        logger.warning("sheets_header_check_failed reason=%s", exc)


def push_lead_result_to_sheet(
    *,
    name: str,
    city: str,
    state: str | None,
    score: int,
    decision: str | None,
    urgency: str,
    whatsapp_message: str | None,
) -> None:
    """Append one row to the configured Google Sheet. Silently skips on any error."""
    sheet = _get_sheet()
    if sheet is None:
        return
    try:
        _ensure_header(sheet)
        row = [
            datetime.now(UTC).isoformat(),
            name,
            city,
            state or "",
            score,
            decision or "",
            urgency,
            whatsapp_message or "",
        ]
        sheet.append_row(row, value_input_option="USER_ENTERED")
        logger.info("sheets_row_appended name=%s score=%s", name, score)
    except Exception as exc:
        logger.warning("sheets_write_failed reason=%s", exc)
